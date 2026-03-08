'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Upload, CheckCircle, AlertCircle, Clock, Link2, Unlink } from 'lucide-react';

interface Customer {
  customer_id: number;
  name: string;
  name_kana: string;
}

interface CustomerOrder {
  customer_order_id: string;
  customer_id: number;
  customer_name: string;
  order_date: string;
  order_amount: number;
  payment_due_date: string;
  payment_status: string;
  deposit_record_id: string | null;
  memo: string | null;
}

interface DepositRecord {
  deposit_record_id: string;
  deposit_date: string;
  depositor_name: string | null;
  amount: number;
  detail1: string | null;
  detail2: string | null;
  matched_order_id: string | null;
  matched_customer_name: string | null;
  matched_order_amount: number | null;
  upload_batch_id: string | null;
}

interface UploadResult {
  total_records: number;
  deposit_only: number;
  auto_matched: number;
  unmatched: number;
  matched_details: Array<{
    deposit_id: string;
    depositor_name: string;
    amount: number;
    order_id: string;
    customer_name: string;
    order_amount: number;
  }>;
  unmatched_deposits: DepositRecord[];
}

export default function CustomersPage() {
  const [activeTab, setActiveTab] = useState<'orders' | 'deposits'>('orders');
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [deposits, setDeposits] = useState<DepositRecord[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isMatchDialogOpen, setIsMatchDialogOpen] = useState(false);
  const [selectedDeposit, setSelectedDeposit] = useState<DepositRecord | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [newOrder, setNewOrder] = useState({
    customer_id: '',
    order_date: new Date().toISOString().split('T')[0],
    order_amount: '',
    payment_due_date: '',
    memo: '',
  });
  const router = useRouter();

  const loadOrders = useCallback(async () => {
    const params: { status?: string } = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    const res = await apiClient.getCustomerOrders(params);
    if (res.data) setOrders(res.data as CustomerOrder[]);
  }, [statusFilter]);

  const loadCustomers = useCallback(async () => {
    const res = await apiClient.getCustomers();
    if (res.data) setCustomers(res.data as Customer[]);
  }, []);

  const loadDeposits = useCallback(async () => {
    const res = await apiClient.getDepositRecords();
    if (res.data) setDeposits(res.data as DepositRecord[]);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) { router.push('/login'); return; }
    loadCustomers();
  }, [router, loadCustomers]);

  useEffect(() => {
    if (activeTab === 'orders') loadOrders();
    else loadDeposits();
  }, [activeTab, statusFilter, loadOrders, loadDeposits]);

  const handleCreateOrder = async () => {
    if (!newOrder.customer_id || !newOrder.order_amount || !newOrder.payment_due_date) return;
    const res = await apiClient.createCustomerOrder({
      customer_id: parseInt(newOrder.customer_id),
      order_date: newOrder.order_date,
      order_amount: parseInt(newOrder.order_amount),
      payment_due_date: newOrder.payment_due_date,
      memo: newOrder.memo || undefined,
    });
    if (res.data) {
      setIsCreateDialogOpen(false);
      setNewOrder({ customer_id: '', order_date: new Date().toISOString().split('T')[0], order_amount: '', payment_due_date: '', memo: '' });
      loadOrders();
    }
  };

  const handleDeleteOrder = async (orderId: string) => {
    if (!confirm('この注文を削除しますか？')) return;
    await apiClient.deleteCustomerOrder(orderId);
    loadOrders();
  };

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setUploadResult(null);
    const res = await apiClient.uploadDepositsCSV(file);
    setIsUploading(false);
    if (res.data) {
      setUploadResult(res.data as UploadResult);
      loadDeposits();
      loadOrders();
    } else {
      alert('CSVアップロードに失敗しました: ' + (res.error || '不明なエラー'));
    }
    e.target.value = '';
  };

  const handleManualMatch = async (depositId: string, orderId: string) => {
    const res = await apiClient.manualMatchDeposit(depositId, orderId);
    if (res.data) {
      setIsMatchDialogOpen(false);
      setSelectedDeposit(null);
      loadDeposits();
      loadOrders();
    } else {
      alert('紐付けに失敗しました: ' + (res.error || ''));
    }
  };

  const handleUnmatch = async (depositId: string) => {
    if (!confirm('紐付けを解除しますか？')) return;
    await apiClient.unmatchDeposit(depositId);
    loadDeposits();
    loadOrders();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'paid':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800"><CheckCircle className="w-3 h-3" />入金済</span>;
      case 'overdue':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800"><AlertCircle className="w-3 h-3" />期限超過</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-800"><Clock className="w-3 h-3" />未入金</span>;
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('ja-JP').format(amount) + '円';
  };

  // 未入金注文リスト（手動紐付けダイアログ用）
  const unpaidOrders = orders.filter(o => o.payment_status !== 'paid');

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">顧客注文管理</h1>
            <Button onClick={() => router.push('/dashboard')} variant="outline">
              ダッシュボードに戻る
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* タブ */}
          <div className="mb-6 flex space-x-4">
            <Button
              variant={activeTab === 'orders' ? 'default' : 'outline'}
              onClick={() => setActiveTab('orders')}
              className={activeTab === 'orders' ? 'text-white' : ''}
            >
              注文管理
            </Button>
            <Button
              variant={activeTab === 'deposits' ? 'default' : 'outline'}
              onClick={() => setActiveTab('deposits')}
              className={activeTab === 'deposits' ? 'text-white' : ''}
            >
              入金チェック
            </Button>
          </div>

          {/* ========== 注文管理タブ ========== */}
          {activeTab === 'orders' && (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center flex-wrap gap-4">
                  <div>
                    <CardTitle>注文一覧</CardTitle>
                    <CardDescription>顧客からの注文を管理します</CardDescription>
                  </div>
                  <div className="flex items-center gap-3">
                    {/* ステータスフィルタ */}
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                      <SelectTrigger className="w-[140px]">
                        <SelectValue placeholder="ステータス" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">すべて</SelectItem>
                        <SelectItem value="unpaid">未入金</SelectItem>
                        <SelectItem value="paid">入金済</SelectItem>
                        <SelectItem value="overdue">期限超過</SelectItem>
                      </SelectContent>
                    </Select>
                    {/* 新規注文ボタン */}
                    <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                      <DialogTrigger asChild>
                        <Button className="text-white">新規注文</Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>新規注文作成</DialogTitle>
                          <DialogDescription>注文情報を入力してください</DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                          <div className="grid grid-cols-4 items-center gap-4">
                            <Label className="text-right">顧客</Label>
                            <Select value={newOrder.customer_id} onValueChange={(v) => setNewOrder({ ...newOrder, customer_id: v })}>
                              <SelectTrigger className="col-span-3">
                                <SelectValue placeholder="顧客を選択" />
                              </SelectTrigger>
                              <SelectContent>
                                {customers.map((c) => (
                                  <SelectItem key={c.customer_id} value={c.customer_id.toString()}>
                                    {c.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="grid grid-cols-4 items-center gap-4">
                            <Label className="text-right">注文日</Label>
                            <Input type="date" value={newOrder.order_date} onChange={(e) => setNewOrder({ ...newOrder, order_date: e.target.value })} className="col-span-3" />
                          </div>
                          <div className="grid grid-cols-4 items-center gap-4">
                            <Label className="text-right">金額</Label>
                            <Input type="number" value={newOrder.order_amount} onChange={(e) => setNewOrder({ ...newOrder, order_amount: e.target.value })} className="col-span-3" placeholder="注文金額（円）" />
                          </div>
                          <div className="grid grid-cols-4 items-center gap-4">
                            <Label className="text-right">入金期限</Label>
                            <Input type="date" value={newOrder.payment_due_date} onChange={(e) => setNewOrder({ ...newOrder, payment_due_date: e.target.value })} className="col-span-3" />
                          </div>
                          <div className="grid grid-cols-4 items-center gap-4">
                            <Label className="text-right">メモ</Label>
                            <Input value={newOrder.memo} onChange={(e) => setNewOrder({ ...newOrder, memo: e.target.value })} className="col-span-3" placeholder="任意" />
                          </div>
                        </div>
                        <div className="flex justify-end">
                          <Button onClick={handleCreateOrder} className="text-white">作成</Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>顧客名</TableHead>
                      <TableHead>注文日</TableHead>
                      <TableHead>金額</TableHead>
                      <TableHead>入金期限</TableHead>
                      <TableHead>ステータス</TableHead>
                      <TableHead>メモ</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-gray-500">注文データがありません</TableCell>
                      </TableRow>
                    ) : (
                      orders.map((order) => (
                        <TableRow key={order.customer_order_id} className={order.payment_status === 'overdue' ? 'bg-red-50' : ''}>
                          <TableCell className="font-medium">{order.customer_name}</TableCell>
                          <TableCell>{order.order_date}</TableCell>
                          <TableCell className="font-mono">{formatAmount(order.order_amount)}</TableCell>
                          <TableCell>{order.payment_due_date}</TableCell>
                          <TableCell>{getStatusBadge(order.payment_status)}</TableCell>
                          <TableCell className="text-sm text-gray-500 max-w-[150px] truncate">{order.memo || '-'}</TableCell>
                          <TableCell>
                            <Button variant="destructive" size="sm" onClick={() => handleDeleteOrder(order.customer_order_id)}>削除</Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* ========== 入金チェックタブ ========== */}
          {activeTab === 'deposits' && (
            <div className="space-y-6">
              {/* CSVアップロード */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Upload className="w-5 h-5" />ゆうちょCSVアップロード</CardTitle>
                  <CardDescription>ゆうちょダイレクトからダウンロードした入出金明細CSVをアップロードして、注文と自動照合します</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors">
                      <Upload className="w-4 h-4" />
                      {isUploading ? 'アップロード中...' : 'CSVファイルを選択'}
                      <input type="file" accept=".csv" onChange={handleCSVUpload} className="hidden" disabled={isUploading} />
                    </label>
                  </div>

                  {/* アップロード結果 */}
                  {uploadResult && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-3">
                      <h3 className="font-semibold text-lg">照合結果</h3>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="bg-white p-3 rounded shadow-sm text-center">
                          <div className="text-2xl font-bold">{uploadResult.total_records}</div>
                          <div className="text-sm text-gray-500">入金件数</div>
                        </div>
                        <div className="bg-green-50 p-3 rounded shadow-sm text-center">
                          <div className="text-2xl font-bold text-green-700">{uploadResult.auto_matched}</div>
                          <div className="text-sm text-green-600">自動照合成功</div>
                        </div>
                        <div className="bg-yellow-50 p-3 rounded shadow-sm text-center">
                          <div className="text-2xl font-bold text-yellow-700">{uploadResult.unmatched}</div>
                          <div className="text-sm text-yellow-600">未照合</div>
                        </div>
                      </div>

                      {/* 照合成功リスト */}
                      {uploadResult.matched_details.length > 0 && (
                        <div>
                          <h4 className="font-medium text-green-700 mb-2">✅ 自動照合成功</h4>
                          <div className="space-y-1">
                            {uploadResult.matched_details.map((m, i) => (
                              <div key={i} className="text-sm bg-green-50 p-2 rounded">
                                {m.depositor_name} → {m.customer_name}（{formatAmount(m.amount)}）
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* 入金記録一覧 */}
              <Card>
                <CardHeader>
                  <CardTitle>入金記録一覧</CardTitle>
                  <CardDescription>アップロードされた入金記録と照合状況</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>入金日</TableHead>
                        <TableHead>振込人名</TableHead>
                        <TableHead>金額</TableHead>
                        <TableHead>照合状況</TableHead>
                        <TableHead>操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {deposits.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-8 text-gray-500">入金記録がありません</TableCell>
                        </TableRow>
                      ) : (
                        deposits.map((dep) => (
                          <TableRow key={dep.deposit_record_id} className={dep.matched_order_id ? 'bg-green-50' : 'bg-yellow-50'}>
                            <TableCell>{dep.deposit_date}</TableCell>
                            <TableCell>{dep.depositor_name || '-'}</TableCell>
                            <TableCell className="font-mono">{formatAmount(dep.amount)}</TableCell>
                            <TableCell>
                              {dep.matched_order_id ? (
                                <span className="inline-flex items-center gap-1 text-sm text-green-700">
                                  <CheckCircle className="w-4 h-4" />
                                  {dep.matched_customer_name}（{dep.matched_order_amount ? formatAmount(dep.matched_order_amount) : ''}）
                                </span>
                              ) : (
                                <span className="text-sm text-yellow-700">未照合</span>
                              )}
                            </TableCell>
                            <TableCell>
                              {dep.matched_order_id ? (
                                <Button variant="outline" size="sm" onClick={() => handleUnmatch(dep.deposit_record_id)}>
                                  <Unlink className="w-3 h-3 mr-1" />解除
                                </Button>
                              ) : (
                                <Button variant="outline" size="sm" onClick={() => { setSelectedDeposit(dep); setIsMatchDialogOpen(true); }}>
                                  <Link2 className="w-3 h-3 mr-1" />紐付け
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              {/* 手動紐付けダイアログ */}
              <Dialog open={isMatchDialogOpen} onOpenChange={setIsMatchDialogOpen}>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>手動紐付け</DialogTitle>
                    <DialogDescription>
                      入金記録を注文に紐付けます
                    </DialogDescription>
                  </DialogHeader>
                  {selectedDeposit && (
                    <div className="space-y-4">
                      <div className="p-3 bg-blue-50 rounded">
                        <div className="text-sm font-medium">入金情報</div>
                        <div className="text-sm">振込人: {selectedDeposit.depositor_name || '-'}</div>
                        <div className="text-sm">金額: {formatAmount(selectedDeposit.amount)}</div>
                        <div className="text-sm">日付: {selectedDeposit.deposit_date}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium mb-2">未入金の注文から選択:</div>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {unpaidOrders.length === 0 ? (
                            <div className="text-sm text-gray-500">未入金の注文がありません</div>
                          ) : (
                            unpaidOrders.map((order) => (
                              <div key={order.customer_order_id} className="flex items-center justify-between p-2 border rounded hover:bg-gray-50">
                                <div>
                                  <div className="text-sm font-medium">{order.customer_name}</div>
                                  <div className="text-xs text-gray-500">{formatAmount(order.order_amount)} / 期限: {order.payment_due_date}</div>
                                </div>
                                <Button size="sm" onClick={() => handleManualMatch(selectedDeposit.deposit_record_id, order.customer_order_id)} className="text-white">
                                  紐付け
                                </Button>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </DialogContent>
              </Dialog>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
