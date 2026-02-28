import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 認証不要のパス（ログイン画面など）
const PUBLIC_PATHS = ['/login'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // パブリックパスはスキップ
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // アクセストークンをCookieから確認
  // ※ フロントエンドはlocalStorageにトークンを保存しているため、
  //   middleware（サーバーサイド）では直接読めない。
  //   代わりにCookieに保存するか、ここではトークン用Cookieを確認する。
  const token = request.cookies.get('access_token')?.value;

  if (!token) {
    // 未認証の場合はログインページへリダイレクト
    const loginUrl = new URL('/login', request.url);
    // リダイレクト後に元のURLへ戻れるようにcallbackパラメータを追加
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * 以下を除く全パスにミドルウェアを適用:
     * - _next/static (静的ファイル)
     * - _next/image (画像最適化)
     * - favicon.ico
     * - public フォルダ内のファイル
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
