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
import { Upload, CheckCircle, Clock, Camera, RefreshCw, CreditCard, XCircle } from 'lucide-react';

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
  transaction_id: string | null;
  depositor_name: string | null;
  amount: number;
  detail1: string | null;
  detail2: string | null;
  balance: number | null;
  upload_batch_id: string | null;
  matched_order_id: string | null;
}

interface MatchedDetail {
  deposit_id: string;
  depositor_name: string;
  amount: number;
  order_id: string;
  customer_name: string;
  order_amount: number;
}

interface PendingMatch {
  deposit_id: string;
  depositor_name: string;
  amount: number;
  order_id: string;
  customer_name: string;
  customer_name_kana: string | null;
  order_amount: number;
}

interface UploadResult {
  total_records: number;
  deposit_only: number;
  auto_matched: number;
  pending_confirmation: number;
  skipped_duplicates: number;
  matched_details: MatchedDetail[];
  pending_matches: PendingMatch[];
}

interface RecognizedOrder {
  customer_name: string;
  order_date: string | null;
  order_amount: number;
  memo: string | null;
}

export default function CustomersPage() {
  const [activeTab, setActiveTab] = useState<'orders' | 'deposits'>('orders');
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [deposits, setDeposits] = useState<DepositRecord[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [newOrder, setNewOrder] = useState({
    customer_id: '',
    order_amount: '',
    memo: '',
  });
  // 画像一括登録
  const [isImageDialogOpen, setIsImageDialogOpen] = useState(false);
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [recognizedOrders, setRecognizedOrders] = useState<RecognizedOrder[]>([]);
  const [isBulkRegistering, setIsBulkRegistering] = useState(false);
  // 部分一致確認
  const [pendingMatches, setPendingMatches] = useState<PendingMatch[]>([]);
  const [currentPendingIndex, setCurrentPendingIndex] = useState(0);
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  // 入金チェック
  const [isCheckingPayments, setIsCheckingPayments] = useState(false);
  // 手動入金設定
  const [isPaymentDialogOpen, setIsPaymentDialogOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<CustomerOrder | null>(null);
  const [selectedDepositId, setSelectedDepositId] = useState<string>('');
  const [isUpdatingPayment, setIsUpdatingPayment] = useState(false);
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
    if (activeTab === 'orders') {
      loadOrders();
      loadDeposits();
    } else {
      loadDeposits();
    }
  }, [activeTab, statusFilter, loadOrders, loadDeposits]);

  const handleCreateOrder = async () => {
    if (!newOrder.customer_id || !newOrder.order_amount) return;
    const res = await apiClient.createCustomerOrder({
      customer_id: parseInt(newOrder.customer_id),
      order_amount: parseInt(newOrder.order_amount),
      memo: newOrder.memo || undefined,
    });
    if (res.data) {
      setIsCreateDialogOpen(false);
      setNewOrder({ customer_id: '', order_amount: '', memo: '' });
      loadOrders();
    }
  };

  const handleDeleteOrder = async (orderId: string) => {
    if (!confirm('この注文を削除しますか？')) return;
    await apiClient.deleteCustomerOrder(orderId);
    loadOrders();
  };

  // 画像認識
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsRecognizing(true);
    setRecognizedOrders([]);
    const res = await apiClient.recognizeOrderImage(file);
    setIsRecognizing(false);
    if (res.data) {
      const data = res.data as { orders: RecognizedOrder[] };
      setRecognizedOrders(data.orders || []);
    } else {
      alert('画像認識に失敗しました: ' + (res.error || '不明なエラー'));
    }
    e.target.value = '';
  };

  // 一括登録
  const handleBulkRegister = async () => {
    const validOrders = recognizedOrders.filter(o => o.customer_name.trim() !== '' && o.order_amount > 0);
    if (validOrders.length === 0) return;
    setIsBulkRegistering(true);
    const res = await apiClient.createCustomerOrdersBulk({
      orders: validOrders.map(o => ({
        customer_name: o.customer_name.trim(),
        order_amount: o.order_amount,
        order_date: o.order_date || undefined,
        memo: o.memo || undefined,
      })),
    });
    setIsBulkRegistering(false);
    if (res.data) {
      setIsImageDialogOpen(false);
      setRecognizedOrders([]);
      loadOrders();
    } else {
      alert('一括登録に失敗しました: ' + (res.error || ''));
    }
  };

  // 認識結果の編集
  const updateRecognizedOrder = (index: number, field: keyof RecognizedOrder, value: string | number | null) => {
    setRecognizedOrders(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleCheckPayments = async () => {
    setIsCheckingPayments(true);
    setUploadResult(null);
    const res = await apiClient.checkPayments();
    setIsCheckingPayments(false);
    if (res.data) {
      const result = res.data as UploadResult;
      setUploadResult(result);
      loadDeposits();
      loadOrders();
      if (result.pending_matches && result.pending_matches.length > 0) {
        setPendingMatches(result.pending_matches);
        setCurrentPendingIndex(0);
        setIsConfirmDialogOpen(true);
      } else if (result.auto_matched === 0 && result.pending_confirmation === 0) {
        alert('照合対象の入金記録が見つかりませんでした。');
        setUploadResult(null);
      }
    } else {
      alert('入金チェックに失敗しました: ' + (res.error || '不明なエラー'));
    }
  };

  const openPaymentDialog = (order: CustomerOrder) => {
    setSelectedOrder(order);
    setSelectedDepositId(order.deposit_record_id || 'none');
    setIsPaymentDialogOpen(true);
  };

  const handleManualPaymentUpdate = async (status: 'paid' | 'unpaid') => {
    if (!selectedOrder) return;
    setIsUpdatingPayment(true);
    const depositId = selectedDepositId && selectedDepositId !== 'none' ? selectedDepositId : null;
    const res = await apiClient.updateOrderPaymentStatus(selectedOrder.customer_order_id, {
      payment_status: status,
      deposit_record_id: status === 'paid' ? depositId : null,
    });
    setIsUpdatingPayment(false);
    if (res.data) {
      setIsPaymentDialogOpen(false);
      setSelectedOrder(null);
      setSelectedDepositId('none');
      loadOrders();
      loadDeposits();
    } else {
      alert('更新に失敗しました: ' + (res.error || '不明なエラー'));
    }
  };

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setUploadResult(null);
    const res = await apiClient.uploadDepositsCSV(file);
    setIsUploading(false);
    if (res.data) {
      const result = res.data as UploadResult;
      setUploadResult(result);
      loadDeposits();
      loadOrders();
      // 部分一致候補がある場合は確認ダイアログを表示
      if (result.pending_matches && result.pending_matches.length > 0) {
        setPendingMatches(result.pending_matches);
        setCurrentPendingIndex(0);
        setIsConfirmDialogOpen(true);
      }
    } else {
      alert('CSVアップロードに失敗しました: ' + (res.error || '不明なエラー'));
    }
    e.target.value = '';
  };

  // 部分一致の確認処理
  const handleConfirmMatch = async () => {
    const current = pendingMatches[currentPendingIndex];
    if (!current) return;
    await apiClient.confirmMatch(current.deposit_id, current.order_id);
    loadOrders();
    loadDeposits();
    goToNextPending();
  };

  const handleSkipMatch = () => {
    goToNextPending();
  };

  const goToNextPending = () => {
    if (currentPendingIndex < pendingMatches.length - 1) {
      setCurrentPendingIndex(prev => prev + 1);
    } else {
      setIsConfirmDialogOpen(false);
      setPendingMatches([]);
      setCurrentPendingIndex(0);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'paid':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800"><CheckCircle className="w-3 h-3" />入金済</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-800"><Clock className="w-3 h-3" />未入金</span>;
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('ja-JP').format(amount) + '円';
  };

  // 入金期限超過かつ未入金かチェック
  const isOverdue = (order: CustomerOrder) => {
    if (order.payment_status === 'paid') return false;
    const today = new Date().toISOString().split('T')[0];
    return order.payment_due_date < today;
  };

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
              入金履歴
            </Button>
          </div>

          {/* ========== 注文管理タブ ========== */}
          {activeTab === 'orders' && (
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                  <div>
                    <CardTitle>注文一覧</CardTitle>
                    <CardDescription>顧客からの注文を管理します</CardDescription>
                  </div>
                  <div className="flex items-center gap-3 flex-wrap">
                    {/* ステータスフィルタ */}
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                      <SelectTrigger className="w-[140px] bg-white">
                        <SelectValue placeholder="ステータス" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        <SelectItem value="all">すべて</SelectItem>
                        <SelectItem value="unpaid">未入金</SelectItem>
                        <SelectItem value="paid">入金済</SelectItem>
                      </SelectContent>
                    </Select>
                    {/* 画像一括登録ボタン */}
                    <Dialog open={isImageDialogOpen} onOpenChange={setIsImageDialogOpen}>
                      <DialogTrigger asChild>
                        <Button variant="outline" className="flex items-center gap-2">
                          <Camera className="w-4 h-4" />画像一括登録
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                        <DialogHeader>
                          <DialogTitle>注文台帳画像から一括登録</DialogTitle>
                          <DialogDescription>注文台帳の画像をアップロードして、注文情報を読み取ります</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div>
                            <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors w-fit">
                              <Camera className="w-4 h-4" />
                              {isRecognizing ? '読み取り中...' : '画像を選択'}
                              <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" disabled={isRecognizing} />
                            </label>
                          </div>
                          {recognizedOrders.length > 0 && (
                            <div className="space-y-3">
                              <h4 className="font-medium">読み取り結果（確認・修正してください）</h4>
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    <TableHead>登録日</TableHead>
                                    <TableHead>顧客</TableHead>
                                    <TableHead>金額</TableHead>
                                    <TableHead>メモ</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {recognizedOrders.map((ro, idx) => (
                                    <TableRow key={idx} className={!ro.customer_name.trim() ? 'bg-yellow-50' : ''}>
                                      <TableCell>
                                        <Input
                                          type="date"
                                          value={ro.order_date || ''}
                                          onChange={(e) => updateRecognizedOrder(idx, 'order_date', e.target.value || null)}
                                          className="w-[140px]"
                                        />
                                      </TableCell>
                                      <TableCell>
                                        <Input
                                          value={ro.customer_name}
                                          onChange={(e) => updateRecognizedOrder(idx, 'customer_name', e.target.value)}
                                          className="w-[160px]"
                                          placeholder="顧客名"
                                        />
                                      </TableCell>
                                      <TableCell>
                                        <Input
                                          type="number"
                                          value={ro.order_amount}
                                          onChange={(e) => updateRecognizedOrder(idx, 'order_amount', parseInt(e.target.value) || 0)}
                                          className="w-[120px]"
                                        />
                                      </TableCell>
                                      <TableCell>
                                        <Input
                                          value={ro.memo || ''}
                                          onChange={(e) => updateRecognizedOrder(idx, 'memo', e.target.value || null)}
                                          className="w-[150px]"
                                        />
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                              <div className="flex items-center justify-end gap-3">
                                {recognizedOrders.some(o => !o.customer_name.trim()) && (
                                  <span className="text-xs text-yellow-600">※顧客名が空の行は登録されません</span>
                                )}
                                <Button onClick={handleBulkRegister} disabled={isBulkRegistering} className="text-white">
                                  {isBulkRegistering ? '登録中...' : `${recognizedOrders.filter(o => o.customer_name.trim() !== '' && o.order_amount > 0).length}件を一括登録`}
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>
                      </DialogContent>
                    </Dialog>
                    {/* 新規注文ボタン */}
                    <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                      <DialogTrigger asChild>
                        <Button className="text-white whitespace-nowrap">新規注文</Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>新規注文作成</DialogTitle>
                          <DialogDescription>注文情報を入力してください（登録日: 今日、入金期限: 10日後が自動設定されます）</DialogDescription>
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
                            <Label className="text-right">金額</Label>
                            <Input type="number" value={newOrder.order_amount} onChange={(e) => setNewOrder({ ...newOrder, order_amount: e.target.value })} className="col-span-3" placeholder="注文金額（円）" />
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
                      <TableHead className="whitespace-nowrap">顧客名</TableHead>
                      <TableHead className="whitespace-nowrap">登録日</TableHead>
                      <TableHead className="whitespace-nowrap">金額</TableHead>
                      <TableHead className="whitespace-nowrap">入金期限</TableHead>
                      <TableHead className="whitespace-nowrap">ステータス</TableHead>
                      <TableHead className="whitespace-nowrap">メモ</TableHead>
                      <TableHead className="whitespace-nowrap">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-gray-500">注文データがありません</TableCell>
                      </TableRow>
                    ) : (
                      orders.map((order) => (
                        <TableRow
                          key={order.customer_order_id}
                          className={`cursor-pointer transition-colors ${isOverdue(order) ? 'bg-red-50 text-red-900 hover:bg-red-100' : 'hover:bg-blue-50'}`}
                          onClick={() => openPaymentDialog(order)}
                        >
                          <TableCell className="font-medium whitespace-nowrap">{order.customer_name}</TableCell>
                          <TableCell className="whitespace-nowrap">{order.order_date}</TableCell>
                          <TableCell className="font-mono whitespace-nowrap">{formatAmount(order.order_amount)}</TableCell>
                          <TableCell className="whitespace-nowrap">{order.payment_due_date}</TableCell>
                          <TableCell>{getStatusBadge(order.payment_status)}</TableCell>
                          <TableCell className="text-sm text-gray-500 max-w-[150px] truncate">{order.memo || '-'}</TableCell>
                          <TableCell>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={(e) => { e.stopPropagation(); handleDeleteOrder(order.customer_order_id); }}
                            >削除</Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* ========== 入金履歴タブ ========== */}
          {activeTab === 'deposits' && (
            <div className="space-y-6">
              {/* CSVアップロード */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Upload className="w-5 h-5" />ゆうちょCSVアップロード</CardTitle>
                  <CardDescription>ゆうちょダイレクトからダウンロードした入出金明細CSVをアップロードします</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 flex-wrap">
                    <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors">
                      <Upload className="w-4 h-4" />
                      {isUploading ? 'アップロード中...' : 'CSVファイルを選択'}
                      <input type="file" accept=".csv" onChange={handleCSVUpload} className="hidden" disabled={isUploading} />
                    </label>
                    <Button
                      variant="outline"
                      className="flex items-center gap-2"
                      onClick={handleCheckPayments}
                      disabled={isCheckingPayments || isUploading}
                    >
                      <RefreshCw className={`w-4 h-4 ${isCheckingPayments ? 'animate-spin' : ''}`} />
                      {isCheckingPayments ? 'チェック中...' : '入金チェック実行'}
                    </Button>
                  </div>

                  {/* アップロード結果 */}
                  {uploadResult && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-3">
                      <h3 className="font-semibold text-lg">取り込み結果</h3>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        <div className="bg-white p-3 rounded shadow-sm text-center">
                          <div className="text-2xl font-bold">{uploadResult.total_records}</div>
                          <div className="text-sm text-gray-500">入金件数</div>
                        </div>
                        <div className="bg-green-50 p-3 rounded shadow-sm text-center">
                          <div className="text-2xl font-bold text-green-700">{uploadResult.auto_matched}</div>
                          <div className="text-sm text-green-600">自動入金確認</div>
                        </div>
                        <div className="bg-yellow-50 p-3 rounded shadow-sm text-center">
                          <div className="text-2xl font-bold text-yellow-700">{uploadResult.pending_confirmation}</div>
                          <div className="text-sm text-yellow-600">要確認</div>
                        </div>
                        {uploadResult.skipped_duplicates > 0 && (
                          <div className="bg-gray-100 p-3 rounded shadow-sm text-center">
                            <div className="text-2xl font-bold text-gray-500">{uploadResult.skipped_duplicates}</div>
                            <div className="text-sm text-gray-400">登録済みスキップ</div>
                          </div>
                        )}
                      </div>

                      {/* 自動照合成功リスト */}
                      {uploadResult.matched_details.length > 0 && (
                        <div>
                          <h4 className="font-medium text-green-700 mb-2">✅ 自動入金確認</h4>
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
                  <CardDescription>CSVから取り込んだ入金記録</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>入金日</TableHead>
                        <TableHead>取引番号</TableHead>
                        <TableHead>振込人名</TableHead>
                        <TableHead>金額</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {deposits.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center py-8 text-gray-500">入金記録がありません</TableCell>
                        </TableRow>
                      ) : (
                        deposits.map((dep) => (
                          <TableRow key={dep.deposit_record_id}>
                            <TableCell>{dep.deposit_date}</TableCell>
                            <TableCell className="text-sm text-gray-500">{dep.transaction_id || '-'}</TableCell>
                            <TableCell>{dep.depositor_name || '-'}</TableCell>
                            <TableCell className="font-mono">{formatAmount(dep.amount)}</TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              {/* 部分一致確認ダイアログ */}
              <Dialog open={isConfirmDialogOpen} onOpenChange={setIsConfirmDialogOpen}>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>入金照合の確認</DialogTitle>
                    <DialogDescription>
                      振込人名と顧客名が部分一致しています。一致していますか？
                      （{currentPendingIndex + 1} / {pendingMatches.length}件）
                    </DialogDescription>
                  </DialogHeader>
                  {pendingMatches[currentPendingIndex] && (
                    <div className="space-y-4">
                      <div className="p-4 bg-yellow-50 rounded-lg space-y-2">
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="font-medium text-gray-500">振込人名:</div>
                          <div className="font-bold">{pendingMatches[currentPendingIndex].depositor_name}</div>
                          <div className="font-medium text-gray-500">顧客名:</div>
                          <div className="font-bold">{pendingMatches[currentPendingIndex].customer_name}</div>
                          {pendingMatches[currentPendingIndex].customer_name_kana && (
                            <>
                              <div className="font-medium text-gray-500">顧客名カナ:</div>
                              <div>{pendingMatches[currentPendingIndex].customer_name_kana}</div>
                            </>
                          )}
                          <div className="font-medium text-gray-500">入金額:</div>
                          <div className="font-mono">{formatAmount(pendingMatches[currentPendingIndex].amount)}</div>
                          <div className="font-medium text-gray-500">注文金額:</div>
                          <div className="font-mono">{formatAmount(pendingMatches[currentPendingIndex].order_amount)}</div>
                        </div>
                      </div>
                      <div className="flex justify-end gap-3">
                        <Button variant="outline" onClick={handleSkipMatch}>スキップ</Button>
                        <Button onClick={handleConfirmMatch} className="text-white bg-green-600 hover:bg-green-700">OK（一致している）</Button>
                      </div>
                    </div>
                  )}
                </DialogContent>
              </Dialog>
            </div>
          )}

          {/* 手動入金設定ダイアログ */}
          <Dialog open={isPaymentDialogOpen} onOpenChange={setIsPaymentDialogOpen}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>入金設定</DialogTitle>
                <DialogDescription>
                  {selectedOrder && `${selectedOrder.customer_name}（${formatAmount(selectedOrder.order_amount)}）の入金ステータスを設定します`}
                </DialogDescription>
              </DialogHeader>
              {selectedOrder && (
                <div className="space-y-4">
                  {/* 現在のステータス */}
                  <div className="p-3 bg-gray-50 rounded-lg text-sm space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">現在のステータス:</span>
                      {getStatusBadge(selectedOrder.payment_status)}
                    </div>
                    {selectedOrder.deposit_record_id && (
                      <div className="text-gray-500">
                        現在の紐付け取引番号: <span className="font-mono text-xs">{deposits.find(d => d.deposit_record_id === selectedOrder.deposit_record_id)?.transaction_id || selectedOrder.deposit_record_id.slice(0, 8) + '...'}</span>
                      </div>
                    )}
                  </div>

                  {/* 未紐付け入金記録の選択テーブル */}
                  <div className="space-y-2">
                    <Label>紐付ける入金記録を選択（任意）</Label>
                    <div className="border rounded-lg overflow-auto max-h-64">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-8"></TableHead>
                            <TableHead>入金日</TableHead>
                            <TableHead>取引番号</TableHead>
                            <TableHead>振込人名</TableHead>
                            <TableHead className="text-right">金額</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {deposits.filter(d => !d.matched_order_id || d.deposit_record_id === selectedOrder.deposit_record_id).length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={5} className="text-center py-4 text-gray-500 text-sm">未紐付けの入金記録がありません</TableCell>
                            </TableRow>
                          ) : (
                            deposits
                              .filter(d => !d.matched_order_id || d.deposit_record_id === selectedOrder.deposit_record_id)
                              .map((dep) => {
                                const isSelected = selectedDepositId === dep.deposit_record_id;
                                const isCurrent = dep.deposit_record_id === selectedOrder.deposit_record_id;
                                return (
                                  <TableRow
                                    key={dep.deposit_record_id}
                                    className={`cursor-pointer transition-colors ${isSelected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'}`}
                                    onClick={() => setSelectedDepositId(isSelected ? 'none' : dep.deposit_record_id)}
                                  >
                                    <TableCell className="pr-0">
                                      <input
                                        type="radio"
                                        readOnly
                                        checked={isSelected}
                                        className="accent-blue-600"
                                      />
                                    </TableCell>
                                    <TableCell className="text-sm">{dep.deposit_date}</TableCell>
                                    <TableCell className="font-mono text-xs text-gray-600">{dep.transaction_id || '-'}</TableCell>
                                    <TableCell className="text-sm">
                                      {dep.depositor_name || '-'}
                                      {isCurrent && <span className="ml-1 text-xs text-blue-600">（現在の紐付け）</span>}
                                    </TableCell>
                                    <TableCell className="text-right font-mono text-sm">{formatAmount(dep.amount)}</TableCell>
                                  </TableRow>
                                );
                              })
                          )}
                        </TableBody>
                      </Table>
                    </div>
                    <p className="text-xs text-gray-500">行をクリックして選択。もう一度クリックで選択解除。選択しない場合はステータスのみ変更されます。</p>
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <Button variant="outline" onClick={() => setIsPaymentDialogOpen(false)}>キャンセル</Button>
                    {selectedOrder.payment_status === 'paid' ? (
                      <Button
                        variant="outline"
                        className="flex items-center gap-1 border-red-300 text-red-600 hover:bg-red-50"
                        onClick={() => handleManualPaymentUpdate('unpaid')}
                        disabled={isUpdatingPayment}
                      >
                        <XCircle className="w-4 h-4" />入金を取り消す
                      </Button>
                    ) : (
                      <Button
                        className="flex items-center gap-1 text-white bg-green-600 hover:bg-green-700"
                        onClick={() => handleManualPaymentUpdate('paid')}
                        disabled={isUpdatingPayment}
                      >
                        <CheckCircle className="w-4 h-4" />入金済にする
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
}
