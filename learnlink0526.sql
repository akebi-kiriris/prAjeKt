-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- 主機： 127.0.0.1
-- 產生時間： 2025-05-26 09:46:18
-- 伺服器版本： 10.4.32-MariaDB
-- PHP 版本： 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 資料庫： `learnlink`
--

-- --------------------------------------------------------

--
-- 資料表結構 `announcements`
--

CREATE TABLE `announcements` (
  `id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `content` text NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `file_path` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `announcements`
--

INSERT INTO `announcements` (`id`, `course_id`, `content`, `created_at`, `file_path`) VALUES
(3, 42, '測試內容', '2025-04-05 14:34:30', ''),
(5, 42, '測試', '2025-04-12 18:36:00', 'uploads/67cbdd108fb5c_Assignment02-113.pdf'),
(7, 42, '文字', '2025-04-24 22:46:12', NULL),
(9, 42, '測試公告', '2025-04-26 11:20:16', NULL);

-- --------------------------------------------------------

--
-- 資料表結構 `announcement_replies`
--

CREATE TABLE `announcement_replies` (
  `id` int(11) NOT NULL,
  `announcement_id` int(11) NOT NULL,
  `reply_content` text NOT NULL,
  `reply_file_path` varchar(255) DEFAULT NULL,
  `replied_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `announcement_replies`
--

INSERT INTO `announcement_replies` (`id`, `announcement_id`, `reply_content`, `reply_file_path`, `replied_at`) VALUES
(1, 13, '測試', NULL, '2025-04-24 22:11:23'),
(2, 17, '測試', 'uploads/replies/680a499d7d50a_Assignment05-113.pdf', '2025-04-24 22:24:29'),
(3, 17, '測試', NULL, '2025-04-24 22:24:41'),
(4, 17, '', 'uploads/replies/680a49adebe68_Assignment05-113.pdf', '2025-04-24 22:24:45'),
(5, 7, '回復', NULL, '2025-04-24 22:46:26');

-- --------------------------------------------------------

--
-- 資料表結構 `class`
--

CREATE TABLE `class` (
  `class_id` int(11) NOT NULL,
  `department` varchar(50) NOT NULL,
  `grade` int(11) NOT NULL CHECK (`grade` between 1 and 4)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `class`
--

INSERT INTO `class` (`class_id`, `department`, `grade`) VALUES
(13, '企業管理學系', 1),
(14, '企業管理學系', 2),
(15, '企業管理學系', 3),
(16, '企業管理學系', 4),
(9, '應用經濟學系', 1),
(10, '應用經濟學系', 2),
(11, '應用經濟學系', 3),
(12, '應用經濟學系', 4),
(5, '科技管理學系', 1),
(6, '科技管理學系', 2),
(7, '科技管理學系', 3),
(8, '科技管理學系', 4),
(21, '行銷與觀光管理學系', 1),
(22, '行銷與觀光管理學系', 2),
(23, '行銷與觀光管理學系', 3),
(24, '行銷與觀光管理學系', 4),
(17, '財務金融學系', 1),
(18, '財務金融學系', 2),
(19, '財務金融學系', 3),
(20, '財務金融學系', 4),
(1, '資訊管理學系', 1),
(2, '資訊管理學系', 2),
(3, '資訊管理學系', 3),
(4, '資訊管理學系', 4);

-- --------------------------------------------------------

--
-- 資料表結構 `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_name` varchar(255) NOT NULL,
  `teacher_id` int(11) NOT NULL,
  `credits` int(11) NOT NULL,
  `course_info` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `courses`
--

INSERT INTO `courses` (`course_id`, `course_name`, `teacher_id`, `credits`, `course_info`) VALUES
(38, '管理學', 6, 3, 'uploads/1741966853_Assignment02-113.pdf'),
(42, '企業資源規劃', 1, 3, 'uploads/1741967050_Assignment02-113.pdf'),
(43, '商業智慧', 1, 3, 'uploads/1742043927_Assignment02-113.pdf');

-- --------------------------------------------------------

--
-- 資料表結構 `groups`
--

CREATE TABLE `groups` (
  `group_id` int(11) NOT NULL,
  `group_name` varchar(100) NOT NULL,
  `group_type` enum('task','class') NOT NULL,
  `group_inviteCode` varchar(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `groups`
--

INSERT INTO `groups` (`group_id`, `group_name`, `group_type`, `group_inviteCode`) VALUES
(1, '畢業專題小組6', 'task', '111111'),
(2, '資訊管理學系-三年甲班', 'class', '222222'),
(3, '作業系統-第9組', 'task', '333333'),
(4, '金融科技概論-第14組', 'task', '444444'),
(5, '系統分析與設計-第9組', 'task', '555555'),
(6, '資訊安全概論-第1組', 'task', '666666'),
(21, '這是一個Group', 'task', '153060'),
(22, 'abc', 'task', '377745'),
(23, 'xyz', 'task', '159040');

-- --------------------------------------------------------

--
-- 資料表結構 `group_members`
--

CREATE TABLE `group_members` (
  `group_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `group_members`
--

INSERT INTO `group_members` (`group_id`, `user_id`) VALUES
(1, 1),
(1, 5),
(1, 7),
(2, 1),
(2, 5),
(3, 5),
(3, 7),
(4, 5),
(5, 5),
(6, 1),
(21, 1),
(22, 1),
(23, 1);

-- --------------------------------------------------------

--
-- 資料表結構 `homework`
--

CREATE TABLE `homework` (
  `homework_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `homework_name` varchar(255) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  `completed` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `homework`
--

INSERT INTO `homework` (`homework_id`, `course_id`, `homework_name`, `created_at`, `start_date`, `end_date`, `file_path`, `user_id`, `completed`) VALUES
(1, 42, '111', '2025-04-28 21:39:26', '2025-04-28', '2025-04-30', NULL, 20, 1),
(19, 42, 'test', '2025-04-30 21:12:44', '2025-04-30', '2025-05-10', NULL, 20, 1),
(26, 42, 'test', '2025-05-06 21:53:52', '2025-05-06', '2025-05-13', NULL, 20, 1),
(28, 42, 'test', '2025-05-07 13:06:16', '2025-05-07', '2025-05-07', NULL, 20, 1),
(29, 42, 'test', '2025-05-12 22:33:43', '2025-05-12', '2025-05-19', NULL, 20, 0);

-- --------------------------------------------------------

--
-- 資料表結構 `homework_status`
--

CREATE TABLE `homework_status` (
  `id` int(11) NOT NULL,
  `homework_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `submitted_at` datetime NOT NULL,
  `file_path` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `homework_status`
--

INSERT INTO `homework_status` (`id`, `homework_id`, `user_id`, `submitted_at`, `file_path`) VALUES
(29, 1, 20, '2025-05-07 07:21:54', 'uploads/1746595314_Assignment05-113.pdf'),
(30, 19, 20, '2025-05-07 07:13:13', 'uploads/1746594793_Assignment05-113.pdf'),
(31, 26, 20, '2025-05-06 16:47:13', 'uploads/1746542833_Assignment05-113.pdf'),
(32, 28, 20, '2025-05-07 07:18:40', 'uploads/1746595120_Assignment04-113.pdf');

-- --------------------------------------------------------

--
-- 資料表結構 `messages`
--

CREATE TABLE `messages` (
  `message_id` int(11) NOT NULL,
  `group_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `content` text NOT NULL,
  `timestamp` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `messages`
--

INSERT INTO `messages` (`message_id`, `group_id`, `user_id`, `content`, `timestamp`) VALUES
(1, 1, 1, '大家好，這是專題小組第6組的討論群，Yee~~', '2025-03-01 13:53:16'),
(2, 1, 5, '收到，最近什麼時候開會？', '2025-03-01 13:53:16'),
(3, 2, 1, '因為3/5系上臨時要開會，所以班會改成12:30開始，在112，請準時！下方開放提名班聚地點~', '2025-03-01 13:53:16'),
(4, 2, 1, '饗A Joy', '2025-03-01 13:54:11'),
(5, 2, 5, '貳樓餐廳', '2025-03-01 14:10:25'),
(11, 6, 1, 'Hi~ ?', '2025-03-01 16:47:55'),
(27, 4, 5, '123', '2025-03-01 21:37:35'),
(28, 1, 1, '3/1 ', '2025-03-01 21:38:28'),
(32, 1, 5, 'www.google.com', '2025-03-08 17:36:29'),
(35, 21, 1, '嘿 大家 歡迎加入我們', '2025-03-08 20:54:23'),
(36, 21, 1, '123', '2025-03-22 20:39:53');

-- --------------------------------------------------------

--
-- 資料表結構 `message_reads`
--

CREATE TABLE `message_reads` (
  `message_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `read_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `message_reads`
--

INSERT INTO `message_reads` (`message_id`, `user_id`, `read_at`) VALUES
(1, 5, '2025-04-12 16:58:10'),
(1, 8, '2025-04-12 14:17:12'),
(2, 5, '2025-04-12 16:58:10'),
(2, 8, '2025-04-12 14:17:12'),
(3, 8, '2025-04-12 14:22:40'),
(4, 8, '2025-04-12 14:22:40'),
(5, 8, '2025-04-12 14:22:40'),
(27, 5, '2025-04-12 17:22:34'),
(27, 8, '2025-04-12 14:22:47'),
(28, 5, '2025-04-12 16:58:10'),
(28, 8, '2025-04-12 14:17:12'),
(32, 5, '2025-04-12 16:58:10'),
(32, 8, '2025-04-12 14:17:12'),
(37, 8, '2025-04-12 14:17:12');

-- --------------------------------------------------------

--
-- 資料表結構 `selected_courses`
--

CREATE TABLE `selected_courses` (
  `user_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `selected_courses`
--

INSERT INTO `selected_courses` (`user_id`, `course_id`) VALUES
(1, 38),
(1, 42),
(1, 43),
(5, 38),
(5, 42),
(5, 43),
(20, 38),
(20, 42),
(20, 43),
(22, 38);

-- --------------------------------------------------------

--
-- 資料表結構 `tasks`
--

CREATE TABLE `tasks` (
  `task_id` int(11) NOT NULL,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `completed` tinyint(1) DEFAULT 0,
  `assignee` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `timeline_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  `task_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `isWork` tinyint(1) NOT NULL,
  `assistant` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- 傾印資料表的資料 `tasks`
--

INSERT INTO `tasks` (`task_id`, `name`, `completed`, `assignee`, `timeline_id`, `created_at`, `start_date`, `end_date`, `task_remark`, `isWork`, `assistant`) VALUES
(7, 'asdas', 0, '', 1, '2025-03-01 09:37:20', '2025-03-04 17:31:00', '2025-03-29 17:31:00', 'dasd', 0, NULL),
(8, 'sd', 0, '', 1, '2025-03-01 09:59:49', '2025-02-23 17:59:00', '2025-04-04 17:59:00', 'asdas', 0, NULL),
(9, 'xsds', 0, '', 1, '2025-03-01 10:03:22', '2025-03-10 18:03:00', '2025-04-03 18:03:00', 'dasd', 0, NULL),
(10, 's', 0, '', 1, '2025-03-01 11:53:17', '2025-03-04 19:53:00', '2025-03-29 19:53:00', 'sd', 0, NULL),
(11, 'sad', 0, '', 1, '2025-03-01 12:28:19', '2025-03-11 20:28:00', '2025-04-05 20:28:00', 'as', 0, NULL),
(12, 'sad', 0, '', 1, '2025-03-01 12:28:26', '2025-03-11 20:28:00', '2025-04-05 20:28:00', 'as', 0, NULL),
(13, 'asdas', 0, '', 3, '2025-03-01 12:35:34', '2025-02-24 20:35:00', '2025-03-28 20:35:00', 'sadasd', 0, NULL),
(14, 'ASD', 0, '', 1, '2025-03-01 13:13:59', '2025-03-03 21:13:00', '2025-04-03 21:13:00', 'SADSAD', 0, NULL),
(15, 'ASDAS', 0, '', 1, '2025-03-01 13:20:54', '2025-04-07 21:18:00', '2025-04-11 12:00:00', 'ASDAS', 0, NULL),
(16, 'Task Name', 0, '', 1, '2025-03-08 08:21:21', '2025-03-01 00:00:00', '2025-03-15 12:00:00', 'Task Remark', 0, NULL),
(26, '3月8號專案', 0, '吳育嘉', 14, '2025-03-08 05:19:10', '2025-03-08 21:19:00', '2025-03-14 21:19:00', 'testes', 0, '123'),
(27, '1213', 0, 'asdda', 15, '2025-03-15 04:50:28', '2025-03-12 20:50:00', '2025-03-28 20:50:00', 'asdasd', 0, 'asdasd'),
(28, 'asd', 1, 'sada', 23, '2025-03-15 05:07:36', '2025-03-13 21:07:00', '2025-03-28 21:07:00', 'asd', 0, 'sdasd'),
(29, 'asd', 0, 'asdas', 23, '2025-03-15 05:08:55', '2025-03-11 21:08:00', '2025-03-28 21:08:00', 'sdasd', 0, 'dasda'),
(35, 'asda', 0, 'as', 46, '2025-03-15 11:43:46', '2025-03-06 03:43:00', '2025-03-28 03:43:00', 'asd', 0, 'sdasd'),
(41, 'sadsad', 0, 'asdsad', 1, '2025-03-20 23:50:09', '2025-03-12 15:50:00', '2025-03-27 15:50:00', 'sadsa', 0, 'asd'),
(44, 'asd', 0, 'asdas', 1, '2025-03-20 23:55:07', '2025-03-11 15:55:00', NULL, 'asd', 1, 'dsad'),
(45, 'asds', 0, 'adsa', 1, '2025-03-20 23:56:44', '2025-03-25 15:56:00', NULL, 'dsad', 1, 'dsa'),
(46, 'dsa', 0, 'dasd', 1, '2025-03-21 00:16:24', '2025-03-04 16:16:00', '2025-04-02 16:16:00', 'das', 0, 'asdsa'),
(52, '0328', 0, 'asdasdas', 49, '2025-03-28 04:43:28', '2025-03-10 20:43:00', '2025-04-11 20:43:00', 'sdasd', 0, 'das'),
(56, 'asdas', 0, 'dasdas', 1, '2025-03-29 04:42:07', '2025-03-24 20:42:00', '2025-03-30 20:42:00', 'asdasd', 0, 'dasd'),
(58, '展示用', 0, '吳育嘉', 55, '2025-03-29 05:16:50', '2025-03-27 21:16:00', '2025-03-30 21:16:00', '測試備註', 0, '無'),
(77, 'wfdsd', 0, 'sdas', 56, '2025-04-04 04:27:03', '2025-04-07 20:26:00', '2025-04-24 20:27:00', 'dasdas', 0, 'dasdas'),
(78, 'asdasd', 0, 'aa', 1, '2025-04-05 05:16:53', '2025-04-08 21:16:00', '2025-04-22 21:16:00', 'asd', 0, 'asd'),
(79, '展示上傳檔案功能', 0, '吳育嘉', 59, '2025-04-12 05:22:20', '2025-04-12 21:22:00', '2025-04-15 21:22:00', '測試測試', 0, '無'),
(80, '完成邀請人員', 0, '我', 62, '2025-04-19 03:53:49', '2025-04-19 19:53:00', '2025-04-28 19:53:00', '哈哈是我啦', 0, '無'),
(81, '任務2', 0, '我', 62, '2025-04-19 04:54:03', '2025-04-22 20:49:00', '2025-04-29 20:49:00', '測試用', 0, NULL),
(82, 'asd', 0, 'asdas', 62, '2025-04-19 04:55:46', '2025-04-17 20:55:00', '2025-04-29 20:55:00', 'das', 0, NULL),
(83, 'asdas', 0, 'das', 62, '2025-04-19 04:56:41', '2025-04-19 20:56:00', '2025-04-29 20:56:00', 'asdas', 0, NULL),
(84, '展示用', 0, '我', 64, '2025-04-19 05:17:17', '2025-04-18 21:17:00', '2025-04-30 21:17:00', '測試測試', 0, '無'),
(85, '我', 0, '0430', 64, '2025-04-30 00:55:26', '2025-04-23 16:55:00', '2025-04-29 16:55:00', '哈哈是我啦', 0, NULL),
(90, '0222', 0, '4562', 64, '2025-04-30 01:12:23', '2025-04-23 17:12:00', '2025-05-06 17:12:00', '哈哈是我啦', 0, NULL),
(91, '我', 0, '我', 64, '2025-04-30 01:13:07', '2025-04-23 17:13:00', '2025-05-06 17:13:00', '是我', 0, NULL),
(92, '我0535', 0, '我', 64, '2025-04-30 01:36:17', '2025-04-23 17:36:00', '2025-05-06 17:36:00', '0536', 0, NULL),
(93, '我', 0, '0537 我', 64, '2025-04-30 01:37:21', '2025-04-23 17:37:00', '2025-05-05 17:37:00', '西西', 0, NULL),
(94, '哈阿', 0, '我', 64, '2025-04-30 01:37:55', '2025-04-17 17:37:00', '2025-04-28 17:37:00', '0537', 0, NULL),
(95, 'asdas', 0, 'dasdas', 53, '2025-04-30 01:41:29', '2025-04-15 17:41:00', '2025-05-06 17:41:00', 'asdasd', 0, NULL),
(96, 'cc', 0, 'ccsaa', 53, '2025-04-30 01:42:42', '2025-04-15 17:42:00', '2025-05-04 17:42:00', 'sdasdas', 0, NULL),
(97, 'asdas', 0, 'sadas', 65, '2025-04-30 05:28:03', '2025-04-21 21:27:00', '2025-05-05 21:28:00', 'asdasd', 0, NULL),
(98, '0430', 0, '吳育嘉', 65, '2025-04-30 05:29:07', '2025-04-23 21:29:00', '2025-05-05 21:29:00', '0928', 0, NULL),
(99, 'sda', 0, 'asda', 3, '2025-05-07 01:36:52', '2025-05-19 17:36:00', '2025-05-30 17:36:00', 'asdas', 0, NULL),
(100, 'haha', 0, '我', 66, '2025-05-07 05:27:40', '2025-05-07 21:27:00', '2025-05-27 21:27:00', '0507', 0, NULL),
(101, 'asda', 1, 'asdasd', 67, '2025-05-07 05:28:09', '2025-05-07 21:28:00', '2025-05-27 21:28:00', 'asdasd', 0, NULL),
(105, '0507專案功能報告', 0, '我', 70, '2025-05-07 05:43:29', '2025-05-07 21:43:00', '2025-05-29 21:43:00', '專案功能報告', 0, NULL),
(106, 'asdasdas', 0, 'dasdasdasd', 70, '2025-05-07 06:24:58', '2025-05-07 22:24:00', '2025-05-21 22:24:00', 'asdas', 0, NULL),
(107, 'haha', 0, '我', 66, '2025-05-13 15:28:57', '2025-05-14 07:28:00', '2025-05-15 07:28:00', '哈哈', 0, NULL),
(108, 'asda', 0, 'sas', 74, '2025-05-14 05:44:39', '2025-05-14 21:44:00', '2025-05-21 21:44:00', '1112', 0, NULL),
(109, 'haha', 0, '114532', 76, '2025-05-21 13:03:16', '2025-05-22 20:57:00', '2025-05-27 20:57:00', 'haha', 0, NULL);

-- --------------------------------------------------------

--
-- 資料表結構 `task_comments`
--

CREATE TABLE `task_comments` (
  `comment_id` int(11) NOT NULL,
  `task_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `task_message` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- 傾印資料表的資料 `task_comments`
--

INSERT INTO `task_comments` (`comment_id`, `task_id`, `user_id`, `task_message`) VALUES
(50, 109, 1, 'hahaha');

-- --------------------------------------------------------

--
-- 資料表結構 `task_uploaded_files`
--

CREATE TABLE `task_uploaded_files` (
  `file_id` int(11) NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `storage_path` varchar(255) NOT NULL,
  `upload_time` datetime DEFAULT current_timestamp(),
  `file_size` bigint(20) NOT NULL,
  `uploader_id` int(11) NOT NULL,
  `task_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `task_uploaded_files`
--

INSERT INTO `task_uploaded_files` (`file_id`, `original_filename`, `storage_path`, `upload_time`, `file_size`, `uploader_id`, `task_id`) VALUES
(12, 'fda055d2572c11df71d54f0c252762d0f703c211.jpg', 'uploads\\c0586d7953374b6cb777a86ba6fe8618.jpg', '2025-05-21 21:03:46', 111270, 1, 109);

-- --------------------------------------------------------

--
-- 資料表結構 `task_users`
--

CREATE TABLE `task_users` (
  `task_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `role` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- 傾印資料表的資料 `task_users`
--

INSERT INTO `task_users` (`task_id`, `user_id`, `role`) VALUES
(109, 1, 0),
(109, 5, 1);

-- --------------------------------------------------------

--
-- 資料表結構 `teachers`
--

CREATE TABLE `teachers` (
  `teacher_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `teachers`
--

INSERT INTO `teachers` (`teacher_id`, `name`, `phone`, `email`, `password`, `created_at`) VALUES
(1, '戴基峯', '1234567890', '1234@gmail.com', '1234', '2025-04-19 10:02:18'),
(2, '李彥賢', '', '', '', '2025-04-19 10:02:18'),
(3, '董和昇', '', '', '', '2025-04-19 10:02:18'),
(4, '張宏義', '', '', '', '2025-04-19 10:02:18'),
(5, '葉進儀', '', '', '', '2025-04-19 10:02:18'),
(6, '徐淑如', '', '', '', '2025-04-19 10:02:18'),
(7, '林土量', '', '', '', '2025-04-19 10:02:18'),
(8, '陶蓓麗', '', '', '', '2025-04-19 10:02:18'),
(9, '施雅月 ', '', '', '', '2025-04-19 10:02:18'),
(10, '林宸堂', '', '', '', '2025-04-19 10:02:18'),
(11, '彭元隆', '', '', '', '2025-04-19 10:02:18');

-- --------------------------------------------------------

--
-- 資料表結構 `timelines`
--

CREATE TABLE `timelines` (
  `timeline_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `progress` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- 傾印資料表的資料 `timelines`
--

INSERT INTO `timelines` (`timeline_id`, `name`, `remark`, `start_date`, `end_date`, `created_at`, `progress`) VALUES
(1, '畢業專題', '很重要', '2025-01-27', '2025-03-07', '2025-02-27 15:10:23', 81.11),
(3, '畢業專題3', '狠狠很重要', '2025-02-03', '2025-03-08', '2025-02-28 14:14:59', 77.56),
(4, '被葉專題四', '4', '2025-03-26', '2025-03-27', '2025-02-28 17:52:57', 0),
(5, 'sdasd', 'asdasda', '2025-02-24', '2025-04-03', '2025-02-28 18:57:12', 12.6),
(6, 'sad', 'sdasd', '2025-03-02', '2025-03-28', '2025-02-28 18:57:52', 0),
(7, '123', '123', '2025-03-06', '2025-03-08', '2025-03-07 09:38:43', 70.09),
(31, 'asda', 'sadas', '2025-03-11', '2025-03-21', '2025-03-15 11:04:09', 47.95),
(46, '03.16', '12315', '2025-03-12', '2025-03-29', '2025-03-15 11:43:38', 22.48),
(47, 'asdas', 'asdas', '2025-02-24', '2025-03-19', '2025-03-22 07:11:40', 100),
(48, 'asd', 'asd', '2025-03-09', '2025-03-26', '2025-03-22 07:12:04', 80.2),
(49, 'dsadsa', 'dasdsadsad', '2025-02-24', '2025-04-05', '2025-03-28 04:43:08', 81.32),
(50, '0329測試用', '測試用專案', '2025-03-29', '2025-03-31', '2025-03-29 03:30:50', 23.99),
(51, '03.29', '03.29', '2025-03-27', '2025-03-30', '2025-03-29 04:02:38', 83.39),
(52, '03.29', '03.29', '2025-03-11', '2025-03-30', '2025-03-29 04:03:14', 97.38),
(53, '03.29', '03.29', '2025-03-12', '2025-03-30', '2025-03-29 04:13:58', 97.28),
(57, 'haha 02', 'haha 02', '2025-04-07', '2025-04-21', '2025-04-04 04:15:19', 0),
(58, 'haha 02', 'haha 02', '2025-04-07', '2025-04-21', '2025-04-04 04:15:44', 0),
(59, '0412-測試', '測試用', '2025-04-12', '2025-04-15', '2025-04-12 05:21:54', 18.56),
(60, '0419-測試用', '哈哈測試', '2025-04-19', '2025-04-29', '2025-04-19 03:49:54', 4.93),
(61, '0419-測試用', '哈哈測試', '2025-04-19', '2025-04-29', '2025-04-19 03:51:52', 4.94),
(63, '0419展示', '測試展示', '2025-04-19', '2025-04-22', '2025-04-19 05:11:40', 18.33),
(64, '0419測試', '展示用', '2025-04-19', '2025-04-21', '2025-04-19 05:16:53', 27.67),
(65, '0430 專案功能', '0917', '2025-04-30', '2025-05-05', '2025-04-30 05:17:36', 11.08),
(66, 'asasdasdasdsadasdasdasdasdasdsa', '測試用而已', '2025-05-05', '2025-05-25', '2025-05-07 02:25:41', 12.17),
(70, '0507', '0507專案功能 haha', '2025-05-07', '2025-05-08', '2025-05-07 05:40:36', 56.99),
(72, 'asda', 'sa', '2025-05-13', '2025-05-16', '2025-05-14 04:49:43', 51.15),
(74, 'asdas', 'asdas', '2025-05-07', '2025-06-06', '2025-05-14 04:51:41', 25.12),
(75, '0521', '測試測試', '2025-05-14', '2025-05-31', '2025-05-21 12:38:46', 44.28),
(76, '0521', 'haha', '2025-05-14', '2025-05-23', '2025-05-21 12:57:23', 83.78),
(77, 'asda', 'asda', '2025-05-20', '2025-05-29', '2025-05-26 06:47:09', 69.81),
(78, '測試測試', 'haha', '2025-05-28', '2025-05-31', '2025-05-26 06:49:41', 0),
(79, 'haha', 'haha', '2025-05-20', '2025-06-06', '2025-05-26 06:50:02', 36.97),
(80, '測試', 'testes', '2025-05-15', '2025-05-30', '2025-05-26 07:12:47', 75.34),
(81, '哈哈', 'haha', '2025-05-21', '2025-06-07', '2025-05-26 07:24:11', 31.23);

-- --------------------------------------------------------

--
-- 資料表結構 `timeline_users`
--

CREATE TABLE `timeline_users` (
  `timeline-users_id` int(11) NOT NULL,
  `timeline_id` int(11) NOT NULL,
  `id` int(11) NOT NULL,
  `role` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- 傾印資料表的資料 `timeline_users`
--

INSERT INTO `timeline_users` (`timeline-users_id`, `timeline_id`, `id`, `role`) VALUES
(1, 1, 1, 0),
(2, 3, 1, 0),
(3, 53, 1, 0),
(8, 58, 12, 0),
(9, 59, 1, 0),
(14, 64, 1, 0),
(15, 64, 5, 1),
(16, 65, 1, 0),
(17, 66, 1, 0),
(21, 70, 1, 0),
(23, 66, 5, 1),
(25, 66, 7, 1),
(27, 1, 7, 1),
(28, 1, 5, 1),
(29, 3, 5, 1),
(30, 3, 7, 1),
(31, 53, 5, 1),
(32, 53, 7, 1),
(33, 59, 7, 1),
(34, 64, 7, 1),
(35, 65, 5, 1),
(36, 65, 7, 1),
(37, 70, 5, 1),
(38, 70, 7, 1),
(39, 59, 5, 1),
(43, 72, 1, 0),
(45, 74, 1, 0),
(46, 75, 1, 0),
(47, 76, 1, 0),
(48, 77, 1, 0),
(49, 78, 1, 0),
(50, 79, 1, 0),
(51, 80, 1, 0),
(52, 81, 1, 0);

-- --------------------------------------------------------

--
-- 資料表結構 `todos`
--

CREATE TABLE `todos` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `type` varchar(50) NOT NULL,
  `deadline` datetime NOT NULL,
  `notes` text DEFAULT NULL,
  `completed` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `todos`
--

INSERT INTO `todos` (`id`, `user_id`, `title`, `type`, `deadline`, `notes`, `completed`) VALUES
(39, 5, '電子化企業實作練習', '📖', '2025-03-19 12:00:00', 'MM模組', 1),
(41, 5, '人工智慧概論', '📝', '2025-03-28 21:00:00', '測試範例', 1),
(43, 5, '畢業專題會議', '🏫', '2025-03-22 21:00:00', '', 1),
(44, 5, '人工智慧概論', '📖', '2025-03-26 23:59:00', 'PP模組', 1),
(45, 5, '人工智慧概論', '📖', '2025-04-03 23:59:00', '作業三', 0);

-- --------------------------------------------------------

--
-- 資料表結構 `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `phone` varchar(11) NOT NULL,
  `email` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `student_id` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `department` varchar(50) NOT NULL,
  `entry_year` varchar(4) NOT NULL,
  `grade` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `users`
--

INSERT INTO `users` (`id`, `name`, `phone`, `email`, `created_at`, `student_id`, `password`, `department`, `entry_year`, `grade`) VALUES
(1, '吳育嘉', '0975194866', 'asd9846284586@gmail.com', '2025-03-15 04:27:13', '1114562', '$2y$10$7k4XMiRbBBGPUcuI8Ae1SOc.BOpOmaj2mN17npQEZ0g00H590QFs2', '', '', 0),
(5, '游承佑', '0977136049', 'chengyu20040506@gmail.com', '2025-02-26 16:38:55', '1114533', '$2y$10$Otbe2pCWNI3tT1x0B0N3VO9mFkiiy9kgbV/gi9T2FGzt3JulOa7iq', '資訊管理學系', '111', 3),
(7, '小吉同學', '0987654321', 'gigibaby@gmail.com', '2025-03-08 08:20:15', '1114548', '$2y$10$fhAohTMUN7tX/Q12VYzHT.km0nG/4HuHLtDVbZHMReqF.93TUKszq', '資訊管理學系', '111', 3),
(20, '吳彥宗', '0123456789', 'asssswd@gmail.com', '2025-04-28 12:22:08', '1114444', '$2y$10$jMpE/uebTlL.i6.tomCGle6.hV05IBPwEWuDCGiZYwK6cgke9ya/e', '', '', 0),
(22, '吳育嘉-2', '0975194866', 'a@gmail.com', '2025-05-25 12:16:40', '123456', '$2y$10$IYJFXlCHrD5Wwi/BLrPTfuC2iiKeMBH.P7qXR6bui.6bRBxoZkbCW', '資訊管理學系', '111', 1);

-- --------------------------------------------------------

--
-- 資料表結構 `user_courses`
--

CREATE TABLE `user_courses` (
  `user_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 已傾印資料表的索引
--

--
-- 資料表索引 `announcements`
--
ALTER TABLE `announcements`
  ADD PRIMARY KEY (`id`),
  ADD KEY `course_id` (`course_id`);

--
-- 資料表索引 `announcement_replies`
--
ALTER TABLE `announcement_replies`
  ADD PRIMARY KEY (`id`),
  ADD KEY `announcement_id` (`announcement_id`);

--
-- 資料表索引 `class`
--
ALTER TABLE `class`
  ADD PRIMARY KEY (`class_id`),
  ADD UNIQUE KEY `department` (`department`,`grade`);

--
-- 資料表索引 `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`),
  ADD KEY `teacher_id` (`teacher_id`);

--
-- 資料表索引 `groups`
--
ALTER TABLE `groups`
  ADD PRIMARY KEY (`group_id`),
  ADD UNIQUE KEY `group_inviteCode` (`group_inviteCode`);

--
-- 資料表索引 `group_members`
--
ALTER TABLE `group_members`
  ADD PRIMARY KEY (`group_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- 資料表索引 `homework`
--
ALTER TABLE `homework`
  ADD PRIMARY KEY (`homework_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `homework_ibfk_2` (`course_id`);

--
-- 資料表索引 `homework_status`
--
ALTER TABLE `homework_status`
  ADD PRIMARY KEY (`id`),
  ADD KEY `homework_id` (`homework_id`),
  ADD KEY `user_id` (`user_id`);

--
-- 資料表索引 `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`message_id`),
  ADD KEY `group_id` (`group_id`),
  ADD KEY `user_id` (`user_id`);

--
-- 資料表索引 `message_reads`
--
ALTER TABLE `message_reads`
  ADD PRIMARY KEY (`message_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- 資料表索引 `selected_courses`
--
ALTER TABLE `selected_courses`
  ADD PRIMARY KEY (`user_id`,`course_id`),
  ADD KEY `course_id` (`course_id`);

--
-- 資料表索引 `tasks`
--
ALTER TABLE `tasks`
  ADD PRIMARY KEY (`task_id`);

--
-- 資料表索引 `task_comments`
--
ALTER TABLE `task_comments`
  ADD PRIMARY KEY (`comment_id`),
  ADD KEY `fk_task_comments_user_id` (`user_id`),
  ADD KEY `fk_task_comments_task_id` (`task_id`);

--
-- 資料表索引 `task_uploaded_files`
--
ALTER TABLE `task_uploaded_files`
  ADD PRIMARY KEY (`file_id`),
  ADD UNIQUE KEY `storage_path` (`storage_path`),
  ADD KEY `uploader_id` (`uploader_id`),
  ADD KEY `task_id` (`task_id`);

--
-- 資料表索引 `teachers`
--
ALTER TABLE `teachers`
  ADD PRIMARY KEY (`teacher_id`);

--
-- 資料表索引 `timelines`
--
ALTER TABLE `timelines`
  ADD PRIMARY KEY (`timeline_id`);

--
-- 資料表索引 `timeline_users`
--
ALTER TABLE `timeline_users`
  ADD PRIMARY KEY (`timeline-users_id`),
  ADD KEY `timeline_id` (`timeline_id`),
  ADD KEY `id` (`id`);

--
-- 資料表索引 `todos`
--
ALTER TABLE `todos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- 資料表索引 `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- 資料表索引 `user_courses`
--
ALTER TABLE `user_courses`
  ADD PRIMARY KEY (`user_id`,`course_id`),
  ADD KEY `course_id` (`course_id`);

--
-- 在傾印的資料表使用自動遞增(AUTO_INCREMENT)
--

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `announcements`
--
ALTER TABLE `announcements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `announcement_replies`
--
ALTER TABLE `announcement_replies`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=45;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `homework`
--
ALTER TABLE `homework`
  MODIFY `homework_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=30;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `homework_status`
--
ALTER TABLE `homework_status`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `tasks`
--
ALTER TABLE `tasks`
  MODIFY `task_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=110;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `task_comments`
--
ALTER TABLE `task_comments`
  MODIFY `comment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=51;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `task_uploaded_files`
--
ALTER TABLE `task_uploaded_files`
  MODIFY `file_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `teachers`
--
ALTER TABLE `teachers`
  MODIFY `teacher_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `timelines`
--
ALTER TABLE `timelines`
  MODIFY `timeline_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=82;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `timeline_users`
--
ALTER TABLE `timeline_users`
  MODIFY `timeline-users_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=53;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `todos`
--
ALTER TABLE `todos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- 已傾印資料表的限制式
--

--
-- 資料表的限制式 `announcements`
--
ALTER TABLE `announcements`
  ADD CONSTRAINT `announcements_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`);

--
-- 資料表的限制式 `courses`
--
ALTER TABLE `courses`
  ADD CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`teacher_id`);

--
-- 資料表的限制式 `homework`
--
ALTER TABLE `homework`
  ADD CONSTRAINT `homework_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `homework_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`);

--
-- 資料表的限制式 `homework_status`
--
ALTER TABLE `homework_status`
  ADD CONSTRAINT `homework_status_ibfk_1` FOREIGN KEY (`homework_id`) REFERENCES `homework` (`homework_id`),
  ADD CONSTRAINT `homework_status_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- 資料表的限制式 `messages`
--
ALTER TABLE `messages`
  ADD CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`group_id`),
  ADD CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- 資料表的限制式 `selected_courses`
--
ALTER TABLE `selected_courses`
  ADD CONSTRAINT `selected_courses_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`);

--
-- 資料表的限制式 `task_comments`
--
ALTER TABLE `task_comments`
  ADD CONSTRAINT `fk_task_comments_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE;

--
-- 資料表的限制式 `task_uploaded_files`
--
ALTER TABLE `task_uploaded_files`
  ADD CONSTRAINT `task_uploaded_files_ibfk_1` FOREIGN KEY (`uploader_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `task_uploaded_files_ibfk_2` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`);

--
-- 資料表的限制式 `todos`
--
ALTER TABLE `todos`
  ADD CONSTRAINT `todos_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- 資料表的限制式 `user_courses`
--
ALTER TABLE `user_courses`
  ADD CONSTRAINT `user_courses_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
