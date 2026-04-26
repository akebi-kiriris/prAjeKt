import re

from models import db
from repositories.knowledge_repository import (
    get_knowledge_document_by_id,
    update_knowledge_document_status,
)


class TextSplitterOperationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TextSplitterService:
    HEADING_PATTERN = re.compile(r"^\s{0,3}#{2,6}\s+")
    CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
    WORD_PATTERN = re.compile(r"[A-Za-z0-9_]+")

    def __init__(self, target_min_tokens=500, target_max_tokens=800, overlap_tokens=100):
        if target_min_tokens <= 0 or target_max_tokens <= 0:
            raise ValueError("target_min_tokens 與 target_max_tokens 必須大於 0")
        if target_min_tokens > target_max_tokens:
            raise ValueError("target_min_tokens 不能大於 target_max_tokens")
        if overlap_tokens < 0:
            raise ValueError("overlap_tokens 不能小於 0")

        self.target_min_tokens = target_min_tokens
        self.target_max_tokens = target_max_tokens
        self.overlap_tokens = overlap_tokens

    def split_document_content(self, user_id, document_id, raw_text):
        document = get_knowledge_document_by_id(user_id=user_id, document_id=document_id)
        if document is None:
            raise TextSplitterOperationError("找不到知識文件", 404)

        try:
            chunks = self.split_text(raw_text)
            return [
                {
                    "chunk_index": index,
                    "content": chunk,
                    "metadata": {
                        "token_count": self.estimate_tokens(chunk),
                    },
                }
                for index, chunk in enumerate(chunks)
            ]
        except Exception as exc:
            self._mark_document_failed(user_id=user_id, document_id=document_id)
            if isinstance(exc, TextSplitterOperationError):
                raise
            raise TextSplitterOperationError("文件解析或切塊失敗，文件已標記為 failed", 422) from exc

    def split_text(self, raw_text):
        if not isinstance(raw_text, str):
            raise ValueError("文件內容格式錯誤")

        normalized_text = raw_text.strip()
        if not normalized_text:
            raise ValueError("文件內容為空")

        heading_blocks = self._split_by_markdown_headings(normalized_text)
        segments = []
        for block in heading_blocks:
            block_tokens = self.estimate_tokens(block)
            if block_tokens <= self.target_max_tokens:
                segments.append(block)
                continue
            segments.extend(self._split_long_block(block))

        chunks = self._build_chunks_with_overlap(segments)
        chunks = [chunk for chunk in chunks if chunk.strip()]
        if not chunks:
            raise ValueError("切塊結果為空")
        return chunks

    @classmethod
    def estimate_tokens(cls, text):
        if not text:
            return 0

        cjk_count = len(cls.CJK_PATTERN.findall(text))
        word_count = len(cls.WORD_PATTERN.findall(text))
        punctuation_count = len(re.findall(r"[^\w\s]", text, flags=re.UNICODE))

        estimated = cjk_count + int(word_count * 1.3) + int(punctuation_count * 0.2)
        return max(1, estimated)

    def _split_by_markdown_headings(self, text):
        lines = text.splitlines(keepends=True)
        blocks = []
        current = []

        for line in lines:
            if self.HEADING_PATTERN.match(line) and current:
                blocks.append("".join(current).strip())
                current = [line]
            else:
                current.append(line)

        if current:
            blocks.append("".join(current).strip())

        return [block for block in blocks if block]

    def _split_long_block(self, block):
        # 長段落先依中文句號與換行細分，仍過長再做硬切。
        primary_parts = [
            part.strip()
            for part in re.split(r"(?<=。)|\n+", block)
            if part and part.strip()
        ]

        if not primary_parts:
            return self._hard_split_by_token_window(block)

        refined = []
        for part in primary_parts:
            if self.estimate_tokens(part) <= self.target_max_tokens:
                refined.append(part)
            else:
                refined.extend(self._hard_split_by_token_window(part))

        return refined

    def _hard_split_by_token_window(self, text):
        windows = []
        current_chars = []
        current_tokens = 0

        for char in text:
            current_chars.append(char)
            current_tokens = self.estimate_tokens("".join(current_chars))
            if current_tokens >= self.target_max_tokens:
                windows.append("".join(current_chars).strip())
                current_chars = []
                current_tokens = 0

        if current_chars:
            windows.append("".join(current_chars).strip())

        return [window for window in windows if window]

    def _build_chunks_with_overlap(self, segments):
        chunks = []
        current_parts = []
        current_tokens = 0

        def flush_current():
            nonlocal current_parts, current_tokens
            if not current_parts:
                return
            chunk_text = "\n".join(part for part in current_parts if part).strip()
            if not chunk_text:
                current_parts = []
                current_tokens = 0
                return
            chunks.append(chunk_text)

            overlap_text = self._extract_tail_for_overlap(chunk_text)
            if overlap_text:
                current_parts = [overlap_text]
                current_tokens = self.estimate_tokens(overlap_text)
            else:
                current_parts = []
                current_tokens = 0

        for segment in segments:
            text = (segment or "").strip()
            if not text:
                continue

            token_count = self.estimate_tokens(text)
            if token_count > self.target_max_tokens:
                for partial in self._hard_split_by_token_window(text):
                    partial_tokens = self.estimate_tokens(partial)
                    if current_parts and current_tokens + partial_tokens > self.target_max_tokens:
                        flush_current()
                    current_parts.append(partial)
                    current_tokens += partial_tokens
                    if current_tokens >= self.target_max_tokens:
                        flush_current()
                continue

            if (
                current_parts
                and current_tokens + token_count > self.target_max_tokens
                and current_tokens >= self.target_min_tokens
            ):
                flush_current()

            current_parts.append(text)
            current_tokens += token_count

        if current_parts:
            final_chunk = "\n".join(part for part in current_parts if part).strip()
            if final_chunk:
                chunks.append(final_chunk)

        if len(chunks) >= 2:
            last_tokens = self.estimate_tokens(chunks[-1])
            if last_tokens < max(1, self.overlap_tokens // 2):
                chunks[-2] = f"{chunks[-2]}\n{chunks[-1]}".strip()
                chunks.pop()

        return chunks

    def _extract_tail_for_overlap(self, chunk_text):
        if self.overlap_tokens == 0:
            return ""

        units = [
            unit.strip()
            for unit in re.split(r"(?<=。)|\n+", chunk_text)
            if unit and unit.strip()
        ]
        if not units:
            return ""

        selected = []
        running_tokens = 0
        for unit in reversed(units):
            selected.insert(0, unit)
            running_tokens += self.estimate_tokens(unit)
            if running_tokens >= self.overlap_tokens:
                break

        return "\n".join(selected).strip()

    def _mark_document_failed(self, user_id, document_id):
        try:
            document = update_knowledge_document_status(
                user_id=user_id,
                document_id=document_id,
                status="failed",
            )
            if document is not None:
                db.session.commit()
        except Exception:
            db.session.rollback()
