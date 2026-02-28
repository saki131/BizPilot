'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { ChevronLeft } from 'lucide-react';

interface MonthlyTotal {
  year_month: string;
  sales_invoice_total: number;
  contractor_invoice_total: number;
  grand_total: number;
}

interface ProductQuantity {
  product_id: number;
  product_name: string;
  display_order: number;
  sales_total_quantity: number;
  contractor_total_quantity: number;
  grand_total_quantity: number;
}

function formatYen(amount: number): string {
  return `¥${amount.toLocaleString('ja-JP')}`;
}

function formatYenOrDash(amount: number): string {
  return amount === 0 ? '—' : `¥${amount.toLocaleString('ja-JP')}`;
}

export default function SalesPage() {
  const router = useRouter();
  const currentYear = new Date().getFullYear();

  const [selectedYear, setSelectedYear] = useState<number>(currentYear);
  const [monthlyTotals, setMonthlyTotals] = useState<MonthlyTotal[]>([]);
  const [productQuantities, setProductQuantities] = useState<ProductQuantity[]>([]);
  const [selectedMonth, setSelectedMonth] = useState<{ year: number; month: number } | null>(null);
  const [loadingTotals, setLoadingTotals] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 認証チェック
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
    }
  }, [router]);

  // 月別合計取得
  const fetchMonthlyTotals = useCallback(async (year: number) => {
    setLoadingTotals(true);
    setError(null);
    setSelectedMonth(null);
    setProductQuantities([]);
    const res = await apiClient.getSalesMonthlyTotals(year);
    setLoadingTotals(false);
    if (res.error) {
      setError(res.error);
    } else {
      setMonthlyTotals(res.data ?? []);
    }
  }, []);

  useEffect(() => {
    fetchMonthlyTotals(selectedYear);
  }, [selectedYear, fetchMonthlyTotals]);

  // 月クリック → 商品別数量取得
  const handleMonthClick = async (ym: string) => {
    const [y, m] = ym.split('-').map(Number);
    setSelectedMonth({ year: y, month: m });
    setLoadingProducts(true);
    setError(null);
    const res = await apiClient.getSalesMonthlyProductQuantities(y, m);
    setLoadingProducts(false);
    if (res.error) {
      setError(res.error);
    } else {
      setProductQuantities(res.data ?? []);
    }
  };

  const handleBack = () => {
    setSelectedMonth(null);
    setProductQuantities([]);
  };

  // 年選択肢: 現在年から3年前まで
  const yearOptions = Array.from({ length: 4 }, (_, i) => currentYear - i);

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      <main className="px-4 py-6 max-w-2xl mx-auto">

        {/* ヘッダー */}
        <div className="flex items-center justify-between mb-5">
          {selectedMonth ? (
            <button
              onClick={handleBack}
              className="flex items-center text-blue-600 font-medium"
            >
              <ChevronLeft className="w-5 h-5 mr-1" />
              月別一覧に戻る
            </button>
          ) : (
            <h1 className="text-xl font-bold text-gray-900">売上表示</h1>
          )}

          {/* 年選択（月別一覧表示時のみ） */}
          {!selectedMonth && (
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {yearOptions.map((y) => (
                <option key={y} value={y}>{y}年</option>
              ))}
            </select>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm mb-4">
            {error}
          </div>
        )}

        {/* ===== 月別合計テーブル ===== */}
        {!selectedMonth && (
          <>
            <p className="text-sm text-gray-500 mb-3">
              月をタップすると商品別の数量を確認できます。
            </p>
            {loadingTotals ? (
              <div className="text-center py-12 text-gray-400">読み込み中...</div>
            ) : monthlyTotals.length === 0 ? (
              <div className="text-center py-12 text-gray-400">{selectedYear}年のデータはありません。</div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                {/* テーブルヘッダー */}
                <div className="grid grid-cols-4 gap-0 bg-gray-100 border-b border-gray-200 text-xs font-semibold text-gray-600">
                  <div className="p-3">年月</div>
                  <div className="p-3 text-right">販売員</div>
                  <div className="p-3 text-right">委託先</div>
                  <div className="p-3 text-right font-bold text-gray-800">合計</div>
                </div>

                {/* テーブル行 */}
                {monthlyTotals.map((row) => {
                  const [, m] = row.year_month.split('-');
                  return (
                    <button
                      key={row.year_month}
                      onClick={() => handleMonthClick(row.year_month)}
                      className="w-full grid grid-cols-4 gap-0 border-b border-gray-100 hover:bg-blue-50 active:bg-blue-100 transition-colors text-left"
                    >
                      <div className="p-3 text-sm font-medium text-blue-600">
                        {parseInt(m, 10)}月
                      </div>
                      <div className="p-3 text-right text-sm text-gray-700">
                        {formatYenOrDash(row.sales_invoice_total)}
                      </div>
                      <div className="p-3 text-right text-sm text-gray-700">
                        {formatYenOrDash(row.contractor_invoice_total)}
                      </div>
                      <div className="p-3 text-right text-sm font-bold text-gray-900">
                        {formatYen(row.grand_total)}
                      </div>
                    </button>
                  );
                })}

                {/* 年間合計行 */}
                {monthlyTotals.length > 0 && (() => {
                  const totalSales = monthlyTotals.reduce((s, r) => s + r.sales_invoice_total, 0);
                  const totalContractor = monthlyTotals.reduce((s, r) => s + r.contractor_invoice_total, 0);
                  const totalGrand = monthlyTotals.reduce((s, r) => s + r.grand_total, 0);
                  return (
                    <div className="grid grid-cols-4 gap-0 bg-gray-50 border-t-2 border-gray-300">
                      <div className="p-3 text-sm font-bold text-gray-800">年間計</div>
                      <div className="p-3 text-right text-sm font-semibold text-gray-800">
                        {formatYen(totalSales)}
                      </div>
                      <div className="p-3 text-right text-sm font-semibold text-gray-800">
                        {formatYen(totalContractor)}
                      </div>
                      <div className="p-3 text-right text-sm font-bold text-gray-900">
                        {formatYen(totalGrand)}
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </>
        )}

        {/* ===== 商品別数量テーブル ===== */}
        {selectedMonth && (
          <>
            <h2 className="text-base font-bold text-gray-800 mb-3">
              {selectedMonth.year}年{selectedMonth.month}月　商品別数量
            </h2>
            {loadingProducts ? (
              <div className="text-center py-12 text-gray-400">読み込み中...</div>
            ) : productQuantities.length === 0 ? (
              <div className="text-center py-12 text-gray-400">この月の明細データはありません。</div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                {/* テーブルヘッダー */}
                <div className="grid grid-cols-4 gap-0 bg-gray-100 border-b border-gray-200 text-xs font-semibold text-gray-600">
                  <div className="p-3 col-span-1">商品名</div>
                  <div className="p-2 text-right">販売員</div>
                  <div className="p-2 text-right">委託先</div>
                  <div className="p-2 text-right font-bold text-gray-800">合計</div>
                </div>

                {/* テーブル行 */}
                {productQuantities.map((row) => (
                  <div
                    key={row.product_id}
                    className="grid grid-cols-4 gap-0 border-b border-gray-100"
                  >
                    <div className="p-3 text-sm text-gray-800 break-all">{row.product_name}</div>
                    <div className="p-2 text-right text-sm text-gray-700">
                      {row.sales_total_quantity === 0 ? '—' : row.sales_total_quantity.toLocaleString()}
                    </div>
                    <div className="p-2 text-right text-sm text-gray-700">
                      {row.contractor_total_quantity === 0 ? '—' : row.contractor_total_quantity.toLocaleString()}
                    </div>
                    <div className="p-2 text-right text-sm font-bold text-gray-900">
                      {row.grand_total_quantity.toLocaleString()}
                    </div>
                  </div>
                ))}

              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
