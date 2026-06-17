export interface User {
  id: number;
  name: string;
  username: string | null;
  email: string;
  phone: string | null;
  avatar?: string | null;
  bio?: string | null;
}

export interface AuthUser {
  id: number;
  name: string;
  username: string | null;
  email: string;
}

export interface AuthLoginResponse {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export interface CurrentUserResponse {
  id: number;
  name: string;
  username: string | null;
  email: string;
  phone: string | null;
}
