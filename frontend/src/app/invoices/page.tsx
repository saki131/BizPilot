'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';

interface SalesInvoice {
  id: number;
  sales_person_id: number;
  sales_person_name: string;
  invoice_number: string;
  start_date: string;
  end_date: string;
  discount_rate_id: number;
  discount_rate: number;
  invoice_date?: string;
  receipt_date?: string;
  non_discountable_amount: number;
  note?: string;
  quota_subtotal: number;
  quota_discount_amount: number;
  quota_total: number;
  non_quota_subtotal: number;
  non_quota_discount_amount: number;
  non_quota_total: number;
  total_amount_ex_tax: number;
  tax_amount: number;
  total_amount_inc_tax: number;
  details: InvoiceDetail[];
}

interface InvoiceDetail {
  id: number;
  product_id: number;
  product_name: string;
  total_quantity: number;
  unit_price: number;
  amount: number;
}

interface SalesPerson {
  id: number;
  name: string;
}

interface Contractor {
  id: number;
  name: string;
}

interface Product {
  id: number;
  name: string;
  price: number;
  quota_target_flag: boolean;
}

interface DiscountRate {
  id: number;
  rate: number;
  threshold_amount: number;
  customer_flag: boolean;
}

interface ContractorInvoice {
  id: number;
  contractor_id: number;
  contractor_name: string;
  invoice_number: string;
  start_date: string;
  end_date: string;
  discount_rate: number;
  invoice_date?: string;
  receipt_date?: string;
  note?: string;
  quota_subtotal: number;
  quota_discount_amount: number;
  quota_total: number;
  non_quota_subtotal: number;
  non_quota_discount_amount: number;
  non_quota_total: number;
  total_amount_ex_tax: number;
  tax_amount: number;
  total_amount_inc_tax: number;
  details: InvoiceDetail[];
}

interface ContractorInvoiceFormData {
  contractor_id: number;
  start_date: string;
  end_date: string;
  invoice_date: string;
  note: string;
  details: {
    product_id: number;
    quantity: number;
    unit_price: number;
  }[];
}

export default function InvoicesPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'sales' | 'contractor'>('sales');
  
  // 販売員請求書用
  const [invoices, setInvoices] = useState<SalesInvoice[]>([]);
  const [salesPersons, setSalesPersons] = useState<SalesPerson[]>([]);
  const [discountRates, setDiscountRates] = useState<DiscountRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showBulkDialog, setShowBulkDialog] = useState(false);
  const [showDiscountDialog, setShowDiscountDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<SalesInvoice | null>(null);
  const [editingInvoice, setEditingInvoice] = useState<Partial<SalesInvoice>>({});
  
  // 委託先請求書用
  const [contractorInvoices, setContractorInvoices] = useState<ContractorInvoice[]>([]);
  const [contractors, setContractors] = useState<Contractor[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [showContractorCreateDialog, setShowContractorCreateDialog] = useState(false);
  const [showContractorDetailDialog, setShowContractorDetailDialog] = useState(false);
  const [showContractorDeleteDialog, setShowContractorDeleteDialog] = useState(false);
  const [selectedContractorInvoice, setSelectedContractorInvoice] = useState<ContractorInvoice | null>(null);
  const [contractorFormData, setContractorFormData] = useState<ContractorInvoiceFormData>({
    contractor_id: 0,
    start_date: '',
    end_date: '',
    invoice_date: '',
    note: '',
    details: []
  });
  
  // Bulk generation form state
  const [closingYear, setClosingYear] = useState<number>(new Date().getFullYear());
  const [closingMonth, setClosingMonth] = useState<number>(new Date().getMonth() + 1);
  const [selectedSalesPersonIds, setSelectedSalesPersonIds] = useState<number[]>([]);
  const [selectAllSalesPersons, setSelectAllSalesPersons] = useState(true);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    salesPersonIds: [] as number[]
  });
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  useEffect(() => {
    if (activeTab === 'sales') {
      fetchInvoices();
      fetchSalesPersons();
      fetchDiscountRates();
    } else {
      fetchContractorInvoices();
      fetchContractors();
      fetchProducts();
    }
  }, [activeTab]);

  const fetchInvoices = async () => {
    try {
      const response = await apiClient.getSalesInvoices();
      if (response.data) {
        console.log('[DEBUG] Invoices from API:', response.data);
        const invoicesData = response.data as SalesInvoice[];
        invoicesData.forEach((inv: any) => {
          console.log(`[DEBUG]   Invoice ${inv.id}: discount_rate=${inv.discount_rate} (type: ${typeof inv.discount_rate}), discount_rate*100=${inv.discount_rate * 100}`);
        });
        setInvoices(invoicesData);
      }
    } catch (error) {
      console.error('Failed to fetch invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSalesPersons = async () => {
    try {
      const response = await apiClient.getSalesPersons();
      if (response.data) {
        setSalesPersons(response.data as SalesPerson[]);
      }
    } catch (error) {
      console.error('Failed to fetch sales persons:', error);
    }
  };

  const fetchDiscountRates = async () => {
    try {
      const response = await apiClient.getDiscountRates();
      if (response.data) {
        console.log('[DEBUG] Discount rates from API:', response.data);
        const ratesData = response.data as DiscountRate[];
        ratesData.forEach((rate: any) => {
          console.log(`[DEBUG]   ID=${rate.id}, rate=${rate.rate} (type: ${typeof rate.rate}), rate*100=${rate.rate * 100}`);
        });
        setDiscountRates(ratesData);
      }
    } catch (error) {
      console.error('Failed to fetch discount rates:', error);
    }
  };

  // 委託先請求書用データ取得関数
  const fetchContractorInvoices = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getContractorInvoices();
      if (response.data) {
        setContractorInvoices(response.data as ContractorInvoice[]);
      }
    } catch (error) {
      console.error('Failed to fetch contractor invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchContractors = async () => {
    try {
      const response = await apiClient.getContractors();
      if (response.data) {
        setContractors(response.data as Contractor[]);
      }
    } catch (error) {
      console.error('Failed to fetch contractors:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await apiClient.getProducts();
      if (response.data) {
        setProducts(response.data as Product[]);
      }
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  const handleCreateContractorInvoice = async () => {
    setGenerating(true);
    try {
      await apiClient.createContractorInvoice(contractorFormData);
      alert('委託先請求書を作成しました');
      setShowContractorCreateDialog(false);
      fetchContractorInvoices();
      // フォームをリセット
      setContractorFormData({
        contractor_id: 0,
        start_date: '',
        end_date: '',
        invoice_date: '',
        note: '',
        details: []
      });
    } catch (error) {
      console.error('Failed to create contractor invoice:', error);
      alert('委託先請求書の作成に失敗しました');
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteContractorInvoice = async () => {
    if (!selectedContractorInvoice) return;
    try {
      await apiClient.deleteContractorInvoice(selectedContractorInvoice.id);
      alert('委託先請求書を削除しました');
      setShowContractorDeleteDialog(false);
      fetchContractorInvoices();
    } catch (error) {
      console.error('Failed to delete contractor invoice:', error);
      alert('委託先請求書の削除に失敗しました');
    }
  };

  const addDetailRow = () => {
    setContractorFormData({
      ...contractorFormData,
      details: [...contractorFormData.details, { product_id: 0, quantity: 1, unit_price: 0 }]
    });
  };

  const removeDetailRow = (index: number) => {
    const newDetails = contractorFormData.details.filter((_, i) => i !== index);
    setContractorFormData({ ...contractorFormData, details: newDetails });
  };

  const updateDetailRow = (index: number, field: string, value: any) => {
    const newDetails = [...contractorFormData.details];
    (newDetails[index] as any)[field] = value;
    
    // 商品IDが変更された場合、単価を自動設定
    if (field === 'product_id') {
      const product = products.find(p => p.id === value);
      if (product) {
        newDetails[index].unit_price = product.price;
      }
    }
    
    setContractorFormData({ ...contractorFormData, details: newDetails });
  };


  const handleBulkGenerate = async () => {
    // Construct closing date as YYYY-MM-20
    const closingDate = `${closingYear}-${closingMonth.toString().padStart(2, '0')}-20`;

    setGenerating(true);
    try {
      const response = await apiClient.bulkGenerateSalesInvoices({
        closing_date: closingDate,
        sales_person_ids: selectAllSalesPersons ? undefined : selectedSalesPersonIds,
      });

      if (response.data) {
        const result = response.data as any;
        alert(
          `請求書を生成しました\n` +
          `生成数: ${result.generated_count}件\n` +
          `スキップ: ${result.skipped_count}件\n` +
          `期間: ${result.period.start_date} ~ ${result.period.end_date}`
        );
        setShowBulkDialog(false);
        fetchInvoices();
        // Reset form - no need to reset year/month
        setSelectedSalesPersonIds([]);
        setSelectAllSalesPersons(true);
      } else {
        alert(response.error || '請求書の生成に失敗しました');
      }
    } catch (error) {
      console.error('Failed to generate invoices:', error);
      alert('請求書の生成に失敗しました');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadPDF = async (invoiceId: number) => {
    try {
      await apiClient.downloadInvoicePDF(invoiceId);
    } catch (error) {
      console.error('Failed to download PDF:', error);
      alert('PDFのダウンロードに失敗しました');
    }
  };

  const handleDeleteInvoice = async () => {
    if (!selectedInvoice) return;

    try {
      await apiClient.deleteSalesInvoice(selectedInvoice.id);
      setShowDeleteDialog(false);
      setSelectedInvoice(null);
      alert('請求書を削除しました');
      await fetchInvoices(); // Refresh the list
    } catch (error) {
      console.error('Failed to delete invoice:', error);
      alert('請求書の削除に失敗しました');
    }
  };

  const handleEditInvoice = () => {
    if (!selectedInvoice) return;
    setEditingInvoice({
      discount_rate_id: selectedInvoice.discount_rate_id,
      note: selectedInvoice.note || '',
    });
    setShowDetailDialog(false);
    setShowEditDialog(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedInvoice) return;

    console.log('送信データ:', editingInvoice);

    try {
      // APIクライアントに編集メソッドを追加する必要があります
      const response = await fetch(`http://172.16.0.71:8002/api/sales-invoices/${selectedInvoice.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(editingInvoice),
      });

      if (response.ok) {
        const updatedInvoice = await response.json();
        console.log('更新後のデータ:', updatedInvoice);
        
        // 請求書リストと詳細画面の両方を更新
        setInvoices(prev => prev.map(inv => 
          inv.id === updatedInvoice.id ? updatedInvoice : inv
        ));
        setSelectedInvoice(updatedInvoice);
        
        setShowEditDialog(false);
        setShowDetailDialog(true); // 詳細画面を再表示
        alert('請求書を更新しました');
      } else {
        const errorData = await response.json();
        console.error('更新エラー:', errorData);
        alert(`更新に失敗しました: ${errorData.detail || '不明なエラー'}`);
      }
    } catch (error) {
      console.error('Failed to update invoice:', error);
      alert('更新に失敗しました');
    }
  };

  const handleChangeDiscountRate = async (newDiscountRateId: number) => {
    if (!selectedInvoice) return;

    try {
      const response = await apiClient.updateInvoiceDiscountRate(
        selectedInvoice.id,
        newDiscountRateId
      );

      if (response.data) {
        alert('割引率を変更しました');
        setShowDiscountDialog(false);
        setSelectedInvoice(null);
        fetchInvoices();
      } else {
        alert(response.error || '割引率の変更に失敗しました');
      }
    } catch (error) {
      console.error('Failed to update discount rate:', error);
      alert('割引率の変更に失敗しました');
    }
  };

  const toggleSalesPerson = (id: number) => {
    setSelectedSalesPersonIds(prev =>
      prev.includes(id) ? prev.filter(spId => spId !== id) : [...prev, id]
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-4">
      <div className="px-4 py-4 max-w-2xl mx-auto">
        {/* タブ切り替え */}
        <div className="mb-4 flex space-x-2">
          <Button
            variant={activeTab === 'sales' ? 'default' : 'outline'}
            onClick={() => setActiveTab('sales')}
            className={activeTab === 'sales' ? 'flex-1 text-white' : 'flex-1'}
          >
            販売員請求書
          </Button>
          <Button
            variant={activeTab === 'contractor' ? 'default' : 'outline'}
            onClick={() => setActiveTab('contractor')}
            className={activeTab === 'contractor' ? 'flex-1 text-white' : 'flex-1'}
          >
            委託先請求書
          </Button>
        </div>

        {/* 販売員請求書タブ */}
        {activeTab === 'sales' && (
          <>
        <Button 
          onClick={() => setShowBulkDialog(true)}
          className="w-full mb-4 h-12 font-semibold bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white"
        >
          一括請求書生成
        </Button>

        {/* フィルター */}
        <Card className="mb-4">
          <CardContent className="p-2">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-semibold text-gray-700">フィルター</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsFilterOpen(!isFilterOpen)}
                className="text-xs"
              >
                {isFilterOpen ? '閉じる ▲' : '開く ▼'}
              </Button>
            </div>
            {isFilterOpen && (
            <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3">
              <div>
                <Label htmlFor="filter_start_date" className="text-sm">請求日（開始）</Label>
                <Input
                  id="filter_start_date"
                  type="date"
                  value={filters.startDate}
                  onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                  className="mt-1 bg-white w-40"
                />
              </div>
              <div>
                <Label htmlFor="filter_end_date" className="text-sm">請求日（終了）</Label>
                <Input
                  id="filter_end_date"
                  type="date"
                  value={filters.endDate}
                  onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
                  className="mt-1 bg-white w-40"
                />
              </div>
              <div>
                <Label className="text-sm">販売員（複数選択可）</Label>
                <div className="mt-2 space-y-2 max-h-40 overflow-y-auto border border-gray-200 rounded-md p-3 bg-white">
                  {salesPersons.map((person) => (
                    <div key={person.id} className="flex items-center">
                      <input
                        type="checkbox"
                        id={`filter_sales_person_${person.id}`}
                        checked={filters.salesPersonIds.includes(person.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFilters({ ...filters, salesPersonIds: [...filters.salesPersonIds, person.id] });
                          } else {
                            setFilters({ ...filters, salesPersonIds: filters.salesPersonIds.filter(id => id !== person.id) });
                          }
                        }}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <label htmlFor={`filter_sales_person_${person.id}`} className="ml-2 text-sm text-gray-700 cursor-pointer">
                        {person.name}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {(filters.startDate || filters.endDate || filters.salesPersonIds.length > 0) && (
              <div className="mt-3 flex justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilters({ startDate: '', endDate: '', salesPersonIds: [] })}
                >
                  フィルタークリア
                </Button>
              </div>
            )}
            </>
            )}
          </CardContent>
        </Card>

        {invoices.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <p className="text-gray-500">請求書がありません</p>
            <p className="text-sm text-gray-400 mt-2">「一括請求書生成」から作成してください</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            {invoices
              .filter((invoice) => {
                // 販売員フィルター（複数選択）
                if (filters.salesPersonIds.length > 0 && !filters.salesPersonIds.includes(invoice.sales_person_id)) {
                  return false;
                }
                // 請求日フィルター（開始日）
                if (filters.startDate && invoice.invoice_date && invoice.invoice_date < filters.startDate) {
                  return false;
                }
                // 請求日フィルター（終了日）
                if (filters.endDate && invoice.invoice_date && invoice.invoice_date > filters.endDate) {
                  return false;
                }
                return true;
              })
              .sort((a, b) => {
                // 請求日の降順でソート（invoice_dateがない場合は最後に）
                if (!a.invoice_date && !b.invoice_date) return 0;
                if (!a.invoice_date) return 1;
                if (!b.invoice_date) return -1;
                return b.invoice_date.localeCompare(a.invoice_date);
              })
              .map((invoice, index) => (
              <div 
                key={invoice.id}
                className={`p-4 ${index !== invoices.length - 1 ? 'border-b border-gray-100' : ''}`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 text-lg mb-1">
                      {invoice.sales_person_name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {invoice.start_date} ~ {invoice.end_date}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-600">
                      ¥{invoice.total_amount_inc_tax.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500">税込</div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button 
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSelectedInvoice(invoice);
                      setShowDetailDialog(true);
                    }}
                    className="flex-1 h-10 text-white bg-gray-600 hover:bg-gray-700 border-0"
                  >
                    📋 明細
                  </Button>
                  <Button 
                    size="sm"
                    onClick={() => handleDownloadPDF(invoice.id)}
                    className="flex-1 h-10 font-medium bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    📄 PDF
                  </Button>
                  <Button 
                    size="sm"
                    variant="destructive"
                    onClick={() => {
                      setSelectedInvoice(invoice);
                      setShowDeleteDialog(true);
                    }}
                    className="h-10 px-3 text-white"
                  >
                    🗑️
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

      {/* Bulk Generation Dialog */}
      <Dialog open={showBulkDialog} onOpenChange={setShowBulkDialog}>
        <DialogContent className="w-[95vw] max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>請求書一括生成</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div>
              <Label className="text-red-600">締め日（必須）</Label>
              <div className="flex gap-2 mt-2">
                    <Select value={closingYear.toString()} onValueChange={(value) => setClosingYear(parseInt(value))}>
                      <SelectTrigger className="w-[120px]">
                        <SelectValue placeholder="年" />
                      </SelectTrigger>
                      <SelectContent className="bg-white z-50">
                        {[2024, 2025, 2026, 2027, 2028].map((year) => (
                          <SelectItem key={year} value={year.toString()}>
                            {year}年
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Select value={closingMonth.toString()} onValueChange={(value) => setClosingMonth(parseInt(value))}>
                      <SelectTrigger className="w-[100px]">
                        <SelectValue placeholder="月" />
                      </SelectTrigger>
                      <SelectContent className="bg-white z-50">
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((month) => (
                          <SelectItem key={month} value={month.toString()}>
                            {month}月
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    期間は自動計算されます（前月21日〜選択月の20日）
                  </p>
                </div>
                
                <div>
                  <Label>販売員選択</Label>
                  <div className="space-y-2 mt-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="select-all"
                        checked={selectAllSalesPersons}
                        onCheckedChange={(checked) => {
                          setSelectAllSalesPersons(checked as boolean);
                          if (checked) {
                            setSelectedSalesPersonIds([]);
                          }
                        }}
                      />
                      <label htmlFor="select-all" className="font-bold">
                        全販売員
                      </label>
                    </div>
                    
                    {!selectAllSalesPersons && (
                      <div className="pl-6 space-y-2 max-h-48 overflow-y-auto border p-2 rounded">
                        {salesPersons.map((sp) => (
                          <div key={sp.id} className="flex items-center space-x-2">
                            <Checkbox
                              id={`sp-${sp.id}`}
                              checked={selectedSalesPersonIds.includes(sp.id)}
                              onCheckedChange={() => toggleSalesPerson(sp.id)}
                            />
                            <label htmlFor={`sp-${sp.id}`}>
                              {sp.name}
                            </label>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-blue-50 p-3 rounded">
                  <p className="text-sm text-blue-800">
                    <strong>割引率自動適用ルール：</strong><br />
                    • ¥400,000以上: 40%<br />
                    • ¥200,000以上: 30%<br />
                    • ¥42,000以上: 20%<br />
                    • ¥42,000未満: 0%（後で10%に変更可能）
                  </p>
                </div>

                <Button 
                  onClick={handleBulkGenerate} 
                  disabled={generating}
                  className="w-full h-12 text-white bg-blue-600 hover:bg-blue-700"
                >
                  {generating ? '生成中...' : '一括生成'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

      {/* Discount Rate Change Dialog */}
      <Dialog open={showDiscountDialog} onOpenChange={setShowDiscountDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>割引率を10%に変更</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <p>この請求書の割引率を0%から10%に変更しますか？</p>
            <p className="text-sm text-gray-500">
              変更後、金額が再計算されます。
            </p>
            <div className="flex gap-2">
              <Button
                onClick={() => {
                  const tenPercentRate = discountRates.find(
                    dr => dr.customer_flag && dr.rate === 0.10
                  );
                  if (tenPercentRate) {
                    handleChangeDiscountRate(tenPercentRate.id);
                  }
                }}
                className="flex-1 text-white bg-blue-600 hover:bg-blue-700"
              >
                変更する
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowDiscountDialog(false);
                  setSelectedInvoice(null);
                }}
                className="flex-1 text-white bg-gray-600 hover:bg-gray-700 border-0"
              >
                キャンセル
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>請求書の削除</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <p>この請求書を削除してもよろしいですか？</p>
            {selectedInvoice && (
              <div className="bg-gray-50 p-3 rounded text-sm space-y-1">
                <p><span className="font-medium">販売員:</span> {selectedInvoice.sales_person_name}</p>
                <p><span className="font-medium">請求期間:</span> {selectedInvoice.start_date} ~ {selectedInvoice.end_date}</p>
                <p><span className="font-medium">税込合計:</span> ¥{(selectedInvoice.total_amount_inc_tax || 0).toLocaleString()}</p>
              </div>
            )}
            <p className="text-sm text-red-600">
              この操作は取り消せません。
            </p>
            <div className="flex gap-2">
              <Button
                onClick={handleDeleteInvoice}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white"
              >
                削除する
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowDeleteDialog(false);
                  setSelectedInvoice(null);
                }}
                className="flex-1 text-white bg-gray-600 hover:bg-gray-700 border-0"
              >
                キャンセル
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Invoice Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold">請求書明細</DialogTitle>
            <DialogDescription className="text-sm text-gray-500">{selectedInvoice?.invoice_number}</DialogDescription>
          </DialogHeader>
          {selectedInvoice && (
            <div className="space-y-6">
              {/* 基本情報セクション */}
              <div className="bg-gray-50 p-5 rounded-lg">
                <h3 className="font-semibold text-lg text-gray-700 mb-4 pb-2 border-b">基本情報</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6">
                  <div className="flex items-center">
                    <span className="text-base text-gray-600 w-32">請求書番号</span>
                    <span className="text-base font-medium text-gray-900">{selectedInvoice.invoice_number}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-base text-gray-600 w-32">販売員</span>
                    <span className="text-base font-medium text-gray-900">{selectedInvoice.sales_person_name}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-base text-gray-600 w-32">請求期間</span>
                    <span className="text-base font-medium text-gray-900">{selectedInvoice.start_date} ~ {selectedInvoice.end_date}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-base text-gray-600 w-32">割引率</span>
                    <span className="text-base font-medium text-gray-900">{((selectedInvoice.discount_rate || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-base text-gray-600 w-32">請求日</span>
                    <span className="text-base font-medium text-gray-900">{selectedInvoice.invoice_date || '-'}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-base text-gray-600 w-32">領収日</span>
                    <span className="text-base font-medium text-gray-900">{selectedInvoice.receipt_date || '-'}</span>
                  </div>
                </div>
                {selectedInvoice.note && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="flex items-start">
                      <span className="text-base text-gray-600 w-32 flex-shrink-0">但（ただし書き）</span>
                      <span className="text-base font-medium text-gray-900">{selectedInvoice.note}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* 商品明細セクション */}
              <div className="bg-white rounded-lg overflow-hidden border border-gray-300">
                <div className="bg-gray-600 px-4 py-2">
                  <h3 className="font-semibold text-sm text-white">商品明細</h3>
                </div>
                <div className="overflow-x-auto max-h-96 overflow-y-auto">
                  <Table>
                    <TableHeader className="sticky top-0 z-10">
                      <TableRow className="bg-gray-100 border-b border-gray-300">
                        <TableHead className="font-semibold text-sm text-gray-700 py-3 px-3 min-w-[150px]">商品名</TableHead>
                        <TableHead className="text-center font-semibold text-sm text-gray-700 py-3 px-2 w-16">数量</TableHead>
                        <TableHead className="text-right font-semibold text-sm text-gray-700 py-3 px-2 w-20">単価</TableHead>
                        <TableHead className="text-right font-semibold text-sm text-gray-700 py-3 px-2 w-24">金額</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(selectedInvoice.details || []).map((detail, index) => (
                        <TableRow 
                          key={detail.id} 
                          className={`border-b border-gray-200 ${
                            index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                          }`}
                        >
                          <TableCell className="text-sm text-gray-900 py-3 px-3 font-medium">
                            {detail.product_name}
                          </TableCell>
                          <TableCell className="text-center text-sm text-gray-900 py-3 px-2">
                            {detail.total_quantity}
                          </TableCell>
                          <TableCell className="text-right text-sm text-gray-700 py-3 px-2">
                            ¥{detail.unit_price.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right font-medium text-sm text-gray-900 py-3 px-2">
                            ¥{detail.amount.toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* 合計セクション */}
              <div className="bg-gray-50 p-5 rounded-lg border-2 border-gray-300">
                <div className="space-y-3">
                  {/* ノルマ対象（青系） */}
                  <div className="bg-blue-100 p-3 rounded-lg border-l-4 border-blue-500">
                    <div className="flex justify-between items-center py-1">
                      <span className="text-sm text-blue-900 font-medium">ノルマ対象小計</span>
                      <span className="text-xl font-bold text-blue-900">
                        ¥{(selectedInvoice.quota_subtotal || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="text-sm text-blue-900 font-medium">ノルマ対象割引額</span>
                      <span className="text-xl font-bold text-red-600">
                        -¥{(selectedInvoice.quota_discount_amount || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-t border-blue-300 pt-2 mt-1">
                      <span className="text-sm text-blue-900 font-semibold">ノルマ対象合計</span>
                      <span className="text-xl font-bold text-blue-900">
                        ¥{(selectedInvoice.quota_total || 0).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  
                  {/* ノルマ対象外（緑系） */}
                  <div className="bg-green-100 p-3 rounded-lg border-l-4 border-green-500">
                    <div className="flex justify-between items-center py-1">
                      <span className="text-sm text-green-900 font-medium">ノルマ対象外小計</span>
                      <span className="text-xl font-bold text-green-900">
                        ¥{(selectedInvoice.non_quota_subtotal || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="text-sm text-green-900 font-medium">ノルマ対象外割引額</span>
                      <span className="text-xl font-bold text-red-600">
                        -¥{(selectedInvoice.non_quota_discount_amount || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-t border-green-300 pt-2 mt-1">
                      <span className="text-sm text-green-900 font-semibold">ノルマ対象外合計</span>
                      <span className="text-xl font-bold text-green-900">
                        ¥{(selectedInvoice.non_quota_total || 0).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  
                  {/* 割引対象外（オレンジ系） */}
                  <div className="bg-orange-100 p-3 rounded-lg border-l-4 border-orange-500">
                    <div className="flex justify-between items-center py-1">
                      <span className="text-sm text-orange-900 font-semibold">割引対象外金額</span>
                      <span className="text-xl font-bold text-orange-900">
                        ¥{(selectedInvoice.non_discountable_amount || 0).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  
                  {/* 合計（グレー系） */}
                  <div className="bg-gray-200 p-3 rounded-lg border border-gray-400 mt-4">
                    <div className="flex justify-between items-center py-1">
                      <span className="text-sm text-gray-700 font-medium">税抜合計</span>
                      <span className="text-xl font-bold text-gray-900">
                        ¥{(selectedInvoice.total_amount_ex_tax || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="text-sm text-gray-700 font-medium">消費税（10%）</span>
                      <span className="text-xl font-bold text-gray-700">
                        ¥{(selectedInvoice.tax_amount || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-t-2 border-gray-500 pt-3 mt-2">
                      <span className="text-base text-gray-800 font-bold">税込合計</span>
                      <span className="text-2xl font-bold text-blue-600">
                        ¥{(selectedInvoice.total_amount_inc_tax || 0).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* ボタンエリア */}
              <div className="flex gap-3 justify-end pt-4 border-t">
                <Button
                  onClick={handleEditInvoice}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6"
                >
                  編集
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowDetailDialog(false);
                    setSelectedInvoice(null);
                  }}
                  className="px-6"
                >
                  閉じる
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Invoice Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="w-[95vw] max-w-md">
          <DialogHeader>
            <DialogTitle>請求書編集</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            {selectedInvoice && (() => {
              const currentRate = discountRates.find(dr => dr.id === selectedInvoice.discount_rate_id);
              const zeroPercentRate = discountRates.find(dr => dr.rate === 0);
              const tenPercentRate = discountRates.find(dr => dr.rate === 0.10);
              const canChangeRate = currentRate && (currentRate.rate === 0 || currentRate.rate === 0.10);
              
              return (
                <>
                  {canChangeRate && zeroPercentRate && tenPercentRate ? (
                    <div>
                      <Label>割引率</Label>
                      <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                        <p className="text-sm text-gray-700 mb-2">現在の割引率: <span className="font-bold">{Math.round((currentRate?.rate || 0) * 100)}%</span></p>
                        <p className="text-sm text-gray-600 mb-3">0%と10%を切り替えできます</p>
                        <select
                          value={editingInvoice.discount_rate_id || selectedInvoice.discount_rate_id}
                          onChange={(e) => setEditingInvoice({...editingInvoice, discount_rate_id: Number(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-md"
                        >
                          <option value={zeroPercentRate.id}>0%</option>
                          <option value={tenPercentRate.id}>10%</option>
                        </select>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <Label>割引率</Label>
                      <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md">
                        <p className="text-sm text-gray-700">現在の割引率: <span className="font-bold">{Math.round((currentRate?.rate || 0) * 100)}%</span></p>
                        <p className="text-xs text-gray-500 mt-1">※割引率は合計金額から自動設定されます</p>
                      </div>
                    </div>
                  )}
                </>
              );
            })()}
            <div>
              <Label>但（ただし書き）</Label>
              <Input
                value={editingInvoice.note || ''}
                onChange={(e) => setEditingInvoice({...editingInvoice, note: e.target.value})}
                placeholder="商品代として"
                className="mt-1"
              />
            </div>
            <div className="flex gap-2 pt-2">
              <Button
                onClick={handleSaveEdit}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium"
              >
                保存
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowEditDialog(false)}
                className="flex-1 text-white bg-gray-600 hover:bg-gray-700 border-0"
              >
                キャンセル
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
          </>
        )}

        {/* 委託先請求書タブ */}
        {activeTab === 'contractor' && (
          <>
            <Button 
              onClick={() => setShowContractorCreateDialog(true)}
              className="w-full mb-4 h-12 font-semibold bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 text-white"
            >
              新規作成
            </Button>

            {/* 委託先請求書一覧 */}
            <Card>
              <CardHeader>
                <CardTitle>委託先請求書一覧</CardTitle>
                <CardDescription>{contractorInvoices.length}件の請求書</CardDescription>
              </CardHeader>
              <CardContent>
                {contractorInvoices.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>委託先請求書がありません</p>
                    <p className="text-sm text-gray-400 mt-2">「新規作成」から作成してください</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {contractorInvoices.map((invoice) => (
                      <div
                        key={invoice.id}
                        className="border rounded-lg p-4 bg-white hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => {
                          setSelectedContractorInvoice(invoice);
                          setShowContractorDetailDialog(true);
                        }}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-semibold text-lg">{invoice.contractor_name}</h3>
                            <p className="text-sm text-gray-600">
                              {invoice.start_date} 〜 {invoice.end_date}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-gray-600">割引率 {invoice.discount_rate}%</p>
                          </div>
                        </div>
                        <div className="border-t pt-2 mt-2">
                          <div className="flex justify-between text-sm">
                            <span>税抜合計</span>
                            <span className="font-semibold">¥{invoice.total_amount_ex_tax.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between text-sm text-gray-600">
                            <span>消費税</span>
                            <span>¥{invoice.tax_amount.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between font-bold mt-1">
                            <span>税込合計</span>
                            <span className="text-blue-600">¥{invoice.total_amount_inc_tax.toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 委託先請求書作成ダイアログ */}
            <Dialog open={showContractorCreateDialog} onOpenChange={setShowContractorCreateDialog}>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>委託先請求書作成</DialogTitle>
                  <DialogDescription>
                    委託先と商品明細を入力してください
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label>委託先</Label>
                    <Select
                      value={contractorFormData.contractor_id.toString()}
                      onValueChange={(value) => setContractorFormData({ ...contractorFormData, contractor_id: parseInt(value) })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="委託先を選択" />
                      </SelectTrigger>
                      <SelectContent>
                        {contractors.map((c) => (
                          <SelectItem key={c.id} value={c.id.toString()}>
                            {c.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>請求期間（開始）</Label>
                      <Input
                        type="date"
                        value={contractorFormData.start_date}
                        onChange={(e) => setContractorFormData({ ...contractorFormData, start_date: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>請求期間（終了）</Label>
                      <Input
                        type="date"
                        value={contractorFormData.end_date}
                        onChange={(e) => setContractorFormData({ ...contractorFormData, end_date: e.target.value })}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label>請求日（任意）</Label>
                    <Input
                      type="date"
                      value={contractorFormData.invoice_date}
                      onChange={(e) => setContractorFormData({ ...contractorFormData, invoice_date: e.target.value })}
                    />
                  </div>
                  
                  <div>
                    <Label>商品明細</Label>
                    <div className="space-y-2 mt-2">
                      {contractorFormData.details.map((detail, index) => (
                        <div key={index} className="flex gap-2 items-end">
                          <div className="flex-1">
                            <Select
                              value={detail.product_id.toString()}
                              onValueChange={(value) => updateDetailRow(index, 'product_id', parseInt(value))}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="商品を選択" />
                              </SelectTrigger>
                              <SelectContent>
                                {products.map((p) => (
                                  <SelectItem key={p.id} value={p.id.toString()}>
                                    {p.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="w-20">
                            <Input
                              type="number"
                              placeholder="数量"
                              value={detail.quantity}
                              onChange={(e) => updateDetailRow(index, 'quantity', parseInt(e.target.value) || 0)}
                            />
                          </div>
                          <div className="w-28">
                            <Input
                              type="number"
                              placeholder="単価"
                              value={detail.unit_price}
                              onChange={(e) => updateDetailRow(index, 'unit_price', parseInt(e.target.value) || 0)}
                            />
                          </div>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => removeDetailRow(index)}
                          >
                            削除
                          </Button>
                        </div>
                      ))}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={addDetailRow}
                        className="w-full"
                      >
                        + 商品を追加
                      </Button>
                    </div>
                  </div>
                  
                  <div>
                    <Label>但（ただし書き）</Label>
                    <Input
                      value={contractorFormData.note}
                      onChange={(e) => setContractorFormData({ ...contractorFormData, note: e.target.value })}
                      placeholder="商品代として"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={handleCreateContractorInvoice}
                    disabled={generating || !contractorFormData.contractor_id || contractorFormData.details.length === 0}
                    className="flex-1 text-white"
                  >
                    {generating ? '作成中...' : '作成'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowContractorCreateDialog(false)}
                    className="flex-1"
                  >
                    キャンセル
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            {/* 委託先請求書詳細ダイアログ */}
            <Dialog open={showContractorDetailDialog} onOpenChange={setShowContractorDetailDialog}>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-2xl font-bold">委託先請求書明細</DialogTitle>
                </DialogHeader>
                {selectedContractorInvoice && (
                  <div className="space-y-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h3 className="font-semibold text-lg mb-2">{selectedContractorInvoice.contractor_name}</h3>
                      <p className="text-sm text-gray-600">請求期間: {selectedContractorInvoice.start_date} 〜 {selectedContractorInvoice.end_date}</p>
                      <p className="text-sm text-gray-600">割引率: {selectedContractorInvoice.discount_rate}%</p>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-2">商品明細</h4>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>商品名</TableHead>
                            <TableHead className="text-right">数量</TableHead>
                            <TableHead className="text-right">単価</TableHead>
                            <TableHead className="text-right">金額</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {selectedContractorInvoice.details.map((detail) => (
                            <TableRow key={detail.id}>
                              <TableCell>{detail.product_name}</TableCell>
                              <TableCell className="text-right">{detail.total_quantity}</TableCell>
                              <TableCell className="text-right">¥{detail.unit_price.toLocaleString()}</TableCell>
                              <TableCell className="text-right font-semibold">¥{detail.amount.toLocaleString()}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                      <div className="flex justify-between">
                        <span>税抜合計</span>
                        <span className="font-semibold">¥{selectedContractorInvoice.total_amount_ex_tax.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>消費税</span>
                        <span>¥{selectedContractorInvoice.tax_amount.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between font-bold text-lg border-t pt-2">
                        <span>税込合計</span>
                        <span className="text-blue-600">¥{selectedContractorInvoice.total_amount_inc_tax.toLocaleString()}</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        variant="destructive"
                        onClick={() => {
                          setShowContractorDetailDialog(false);
                          setShowContractorDeleteDialog(true);
                        }}
                        className="flex-1 text-white"
                      >
                        削除
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setShowContractorDetailDialog(false)}
                        className="flex-1"
                      >
                        閉じる
                      </Button>
                    </div>
                  </div>
                )}
              </DialogContent>
            </Dialog>

            {/* 削除確認ダイアログ */}
            <Dialog open={showContractorDeleteDialog} onOpenChange={setShowContractorDeleteDialog}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>委託先請求書の削除</DialogTitle>
                </DialogHeader>
                <p>この委託先請求書を削除してもよろしいですか？</p>
                <div className="flex gap-2 mt-4">
                  <Button
                    variant="destructive"
                    onClick={handleDeleteContractorInvoice}
                    className="flex-1 text-white"
                  >
                    削除
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowContractorDeleteDialog(false)}
                    className="flex-1"
                  >
                    キャンセル
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </>
        )}
      </div>
    </div>
  );
}
