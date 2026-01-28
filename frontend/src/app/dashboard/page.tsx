'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    // For now, just set a dummy user
    setUser({ username: 'admin' });
  }, [router]);

  const handleLogout = async () => {
    await apiClient.logout();
    router.push('/login');
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-4">
      <main className="px-4 py-6 max-w-2xl mx-auto">
        <div className="space-y-3">
          {/* Menu List */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <button 
              className="w-full flex items-center justify-between p-4 border-b border-gray-100 active:bg-gray-50"
              onClick={() => router.push('/masters')}
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 text-lg">📋</span>
                </div>
                <div className="text-left">
                  <div className="font-medium text-gray-900">マスタ管理</div>
                  <div className="text-sm text-gray-500">営業担当・商品・契約者の管理</div>
                </div>
              </div>
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>

            <button 
              className="w-full flex items-center justify-between p-4 border-b border-gray-100 active:bg-gray-50"
              onClick={() => router.push('/delivery-notes')}
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 text-lg">📦</span>
                </div>
                <div className="text-left">
                  <div className="font-medium text-gray-900">納品書管理</div>
                  <div className="text-sm text-gray-500">納品書の作成・編集・管理</div>
                </div>
              </div>
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>

            <button 
              className="w-full flex items-center justify-between p-4 active:bg-gray-50"
              onClick={() => router.push('/invoices')}
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 text-lg">💰</span>
                </div>
                <div className="text-left">
                  <div className="font-medium text-gray-900">請求書生成</div>
                  <div className="text-sm text-gray-500">納品書から請求書を生成</div>
                </div>
              </div>
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          {/* Quick Stats */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-500 rounded-lg shadow-md p-5 text-white">
            <div className="text-sm mb-1 font-medium">ようこそ</div>
            <div className="text-2xl font-bold">{user.username}</div>
          </div>
        </div>
      </main>
    </div>
  );
}