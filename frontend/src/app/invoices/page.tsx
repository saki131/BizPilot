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
  id: string;
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
  id: string;
  product_id: number;
  product_name: string;
  total_quantity: number;
  unit_price: number;
  amount: number;
}

interface SalesPerson {
  sales_person_id: number;
  name: string;
  display_order: number;
}

interface Contractor {
  contractor_id: number;
  name: string;
  display_order: number;
}

interface Product {
  product_id: number;
  name: string;
  price: number;
  display_order: number;
  quota_target_flag: boolean;
}

interface DiscountRate {
  discount_rate_id: number;
  rate: number;
  threshold_amount: number;
  sales_person_flag: boolean;
}

interface ContractorInvoice {
  id: string;
  contractor_id: number;
  contractor_name: string;
  invoice_number: string;
  start_date?: string;
  end_date?: string;
  discount_rate: number;
  invoice_date?: string;
  receipt_date?: string;
  note?: string;
  non_discountable_amount: number;
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
  tax_rate_id: number;
  invoice_date: string;
  receipt_date?: string;
  note: string;
  details: {
    product_id: number;
    total_quantity: number;
    unit_price: number;
  }[];
}

interface TaxRate {
  tax_rate_id: number;
  rate: number;
  display_name: string;
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
  const [affectedBillingDates, setAffectedBillingDates] = useState<string[]>([]);
  
  // 委託先請求書用
  const [contractorInvoices, setContractorInvoices] = useState<ContractorInvoice[]>([]);
  const [contractors, setContractors] = useState<Contractor[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [taxRates, setTaxRates] = useState<TaxRate[]>([]);
  const [showContractorCreateDialog, setShowContractorCreateDialog] = useState(false);
  const [showContractorDetailDialog, setShowContractorDetailDialog] = useState(false);
  const [showContractorDeleteDialog, setShowContractorDeleteDialog] = useState(false);
  const [showContractorEditDialog, setShowContractorEditDialog] = useState(false);
  const [selectedContractorInvoice, setSelectedContractorInvoice] = useState<ContractorInvoice | null>(null);
  const [editingContractorInvoice, setEditingContractorInvoice] = useState<{
    contractor_id: number;
    invoice_date: string;
    receipt_date?: string;
    note: string;
    details: {
      product_id: number;
      total_quantity: number;
      unit_price: number;
    }[];
  }>({
    contractor_id: 0,
    invoice_date: '',
    receipt_date: '',
    note: '',
    details: []
  });
  const [contractorFormData, setContractorFormData] = useState<ContractorInvoiceFormData>({
    contractor_id: 0,
    tax_rate_id: 0,
    invoice_date: (() => {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      return `${year}-${month}-20`;
    })(),
    receipt_date: '',
    note: '御品代として',
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
  const [contractorFilters, setContractorFilters] = useState({
    startDate: '',
    endDate: '',
    contractorIds: [] as number[]
  });
  const [isContractorFilterOpen, setIsContractorFilterOpen] = useState(false);

  useEffect(() => {
    if (activeTab === 'sales') {
      fetchInvoices();
      fetchSalesPersons();
      fetchDiscountRates();
    } else {
      fetchContractorInvoices();
      fetchContractors();
      fetchProducts();
      fetchTaxRates();
    }
    
    // localStorageから影響を受けた締め日を読み込み
    const storedDates = localStorage.getItem('affectedBillingDates');
    if (storedDates) {
      setAffectedBillingDates(JSON.parse(storedDates));
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
          console.log(`[DEBUG]   ID=${rate.discount_rate_id}, rate=${rate.rate} (type: ${typeof rate.rate}), rate*100=${rate.rate * 100}`);
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

  const fetchTaxRates = async () => {
    try {
      const response = await apiClient.getTaxRates();
      if (response.data) {
        const rates = response.data as TaxRate[];
        setTaxRates(rates);
        // デフォルトの税率(10%)を設定
        const defaultRate = rates.find(r => r.rate === 0.1);
        if (defaultRate && contractorFormData.tax_rate_id === 0) {
          setContractorFormData(prev => ({
            ...prev,
            tax_rate_id: defaultRate.tax_rate_id
          }));
        }
      }
    } catch (error) {
      console.error('Failed to fetch tax rates:', error);
    }
  };

  const handleCreateContractorInvoice = async () => {
    // バリデーション
    if (!contractorFormData.contractor_id) {
      alert('委託先を選択してください');
      return;
    }
    if (!contractorFormData.tax_rate_id) {
      alert('税率を選択してください');
      return;
    }
    if (!contractorFormData.invoice_date) {
      alert('請求日を入力してください');
      return;
    }
    if (contractorFormData.details.length === 0) {
      alert('商品明細を追加してください');
      return;
    }
    
    setGenerating(true);
    try {
      await apiClient.createContractorInvoice(contractorFormData);
      alert('委託先請求書を作成しました');
      setShowContractorCreateDialog(false);
      fetchContractorInvoices();
      // フォームをリセット
      const defaultTaxRate = taxRates.find(r => r.rate === 0.1);
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      setContractorFormData({
        contractor_id: 0,
        tax_rate_id: defaultTaxRate?.tax_rate_id || 0,
        invoice_date: `${year}-${month}-20`,
        receipt_date: '',
        note: '御品代として',
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
      details: [...contractorFormData.details, { product_id: 0, total_quantity: 1, unit_price: 0 }]
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
      const product = products.find(p => p.product_id === value);
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
        
        // 生成した締め日をaffectedBillingDatesから削除
        const updatedDates = affectedBillingDates.filter(date => date !== closingDate);
        setAffectedBillingDates(updatedDates);
        localStorage.setItem('affectedBillingDates', JSON.stringify(updatedDates));
        
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

  const handleDownloadPDF = async (invoiceId: string) => {
    try {
      await apiClient.downloadInvoicePDF(invoiceId);
    } catch (error) {
      console.error('Failed to download PDF:', error);
      alert('PDFのダウンロードに失敗しました');
    }
  };

  const handleDownloadReceiptPDF = async (invoiceId: string) => {
    try {
      await apiClient.downloadSalesReceiptPDF(invoiceId);
    } catch (error) {
      console.error('Failed to download receipt PDF:', error);
      alert('領収書PDFのダウンロードに失敗しました');
    }
  };

  const handleDownloadContractorPDF = async (invoiceId: string) => {
    try {
      await apiClient.downloadContractorInvoicePDF(invoiceId);
    } catch (error) {
      console.error('Failed to download PDF:', error);
      alert('PDFのダウンロードに失敗しました');
    }
  };

  const handleDownloadContractorReceiptPDF = async (invoiceId: string) => {
    try {
      await apiClient.downloadContractorReceiptPDF(invoiceId);
    } catch (error) {
      console.error('Failed to download contractor receipt PDF:', error);
      alert('領収書PDFのダウンロードに失敗しました');
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
      const response = await apiClient.updateInvoice(selectedInvoice.id, editingInvoice);

      if (response.data) {
        const updatedInvoice = response.data as SalesInvoice;
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
        console.error('更新エラー:', response.error);
        alert(`更新に失敗しました: ${response.error || '不明なエラー'}`);
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

  const handleEditContractorInvoice = () => {
    if (!selectedContractorInvoice) return;
    setEditingContractorInvoice({
      contractor_id: selectedContractorInvoice.contractor_id,
      invoice_date: selectedContractorInvoice.invoice_date || '',
      note: selectedContractorInvoice.note || '',
      details: selectedContractorInvoice.details.map(d => ({
        product_id: d.product_id,
        total_quantity: d.total_quantity,
        unit_price: d.unit_price
      }))
    });
    setShowContractorDetailDialog(false);
    setShowContractorEditDialog(true);
  };

  const handleSaveContractorEdit = async () => {
    if (!selectedContractorInvoice || !editingContractorInvoice) return;

    setGenerating(true);
    try {
      // 明細のバリデーションと単価の自動設定
      const details = (editingContractorInvoice.details || selectedContractorInvoice.details).map((d: any) => {
        const product = products.find(p => p.product_id === d.product_id);
        const unitPrice = d.unit_price || (product?.price || 0);
        
        return {
          product_id: d.product_id,
          total_quantity: d.total_quantity,
          unit_price: unitPrice
        };
      });

      const updateData = {
        contractor_id: editingContractorInvoice.contractor_id,
        invoice_date: editingContractorInvoice.invoice_date,
        receipt_date: editingContractorInvoice.receipt_date,
        note: editingContractorInvoice.note,
        details
      };

      const response = await apiClient.updateContractorInvoice(
        selectedContractorInvoice.id,
        updateData
      );

      if (response.data) {
        const updatedInvoice = response.data as ContractorInvoice;
        
        setContractorInvoices(prev => prev.map(inv => 
          inv.id === updatedInvoice.id ? updatedInvoice : inv
        ));
        setSelectedContractorInvoice(updatedInvoice);
        
        setShowContractorEditDialog(false);
        setShowContractorDetailDialog(true);
        alert('委託先請求書を更新しました');
        fetchContractorInvoices();
      } else {
        alert(response.error || '更新に失敗しました');
      }
    } catch (error) {
      console.error('Failed to update contractor invoice:', error);
      alert('更新に失敗しました');
    } finally {
      setGenerating(false);
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
        {/* 影響を受けた締め日のアラート */}
        {affectedBillingDates.length > 0 && (
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-yellow-800 mb-1">
                  請求書の再反映が必要な締め日
                </h3>
                <div className="flex flex-wrap gap-2">
                  {affectedBillingDates.sort().map((date) => (
                    <span key={date} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                      {new Date(date).toLocaleDateString('ja-JP', { year: 'numeric', month: 'long', day: 'numeric' })}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        
        <Button 
          onClick={() => setShowBulkDialog(true)}
          className="w-full mb-4 h-12 font-semibold bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white"
        >
          一括請求書反映
        </Button>

        {/* フィルター */}
        <Card className="mb-4">
          <CardContent className="p-2">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-semibold text-gray-700">検索</h3>
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
                    <div key={person.sales_person_id} className="flex items-center">
                      <input
                        type="checkbox"
                        id={`filter_sales_person_${person.sales_person_id}`}
                        checked={filters.salesPersonIds.includes(person.sales_person_id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFilters({ ...filters, salesPersonIds: [...filters.salesPersonIds, person.sales_person_id] });
                          } else {
                            setFilters({ ...filters, salesPersonIds: filters.salesPersonIds.filter(id => id !== person.sales_person_id) });
                          }
                        }}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <label htmlFor={`filter_sales_person_${person.sales_person_id}`} className="ml-2 text-sm text-gray-700 cursor-pointer">
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
                  検索条件クリア
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
                    📄 請求書PDF
                  </Button>
                  <Button 
                    size="sm"
                    onClick={() => handleDownloadReceiptPDF(invoice.id)}
                    className="flex-1 h-10 font-medium bg-green-600 hover:bg-green-700 text-white"
                  >
                    🧾 領収書PDF
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
                          <div key={sp.sales_person_id} className="flex items-center space-x-2">
                            <Checkbox
                              id={`sp-${sp.sales_person_id}`}
                              checked={selectedSalesPersonIds.includes(sp.sales_person_id)}
                              onCheckedChange={() => toggleSalesPerson(sp.sales_person_id)}
                            />
                            <label htmlFor={`sp-${sp.sales_person_id}`}>
                              {sp.name}
                            </label>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
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
                    dr => dr.sales_person_flag && dr.rate === 0.10
                  );
                  if (tenPercentRate) {
                    handleChangeDiscountRate(tenPercentRate.discount_rate_id);
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
          </DialogHeader>
          {selectedInvoice && (
            <div className="space-y-6">
              {/* 基本情報セクション */}
              <div className="bg-gray-50 p-5 rounded-lg">
                <h3 className="font-semibold text-lg text-gray-700 mb-4 pb-2 border-b">基本情報</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6">
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
            {selectedInvoice && (
              <>
                <div>
                  <Label>販売員</Label>
                  <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md">
                    <p className="text-sm font-medium text-gray-900">{selectedInvoice.sales_person_name}</p>
                  </div>
                </div>
                <div>
                  <Label>割引率</Label>
                  <select
                    value={editingInvoice.discount_rate_id || selectedInvoice.discount_rate_id}
                    onChange={(e) => setEditingInvoice({...editingInvoice, discount_rate_id: Number(e.target.value)})}
                    className="w-full px-3 py-2 mt-2 border rounded-md bg-white"
                  >
                    {discountRates
                      .filter(dr => dr.sales_person_flag)
                      .sort((a, b) => a.rate - b.rate)
                      .map((rate) => (
                        <option key={rate.discount_rate_id} value={rate.discount_rate_id}>
                          {rate.rate >= 1 ? Math.round(rate.rate) : Math.round(rate.rate * 100)}%
                        </option>
                      ))}
                  </select>
                </div>
              </>
            )}
            <div>
              <Label>領収日</Label>
              <Input
                type="date"
                value={editingInvoice.receipt_date || selectedInvoice?.receipt_date || ''}
                onChange={(e) => setEditingInvoice({...editingInvoice, receipt_date: e.target.value})}
                className="mt-1"
              />
            </div>
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
            {/* フィルター */}
            <Card className="mb-4">
              <CardContent className="p-2">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-gray-700">検索</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsContractorFilterOpen(!isContractorFilterOpen)}
                    className="text-xs"
                  >
                    {isContractorFilterOpen ? '閉じる ▲' : '開く ▼'}
                  </Button>
                </div>
                {isContractorFilterOpen && (
                <>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3">
                  <div>
                    <Label htmlFor="contractor_filter_start_date" className="text-sm">請求日（開始）</Label>
                    <Input
                      id="contractor_filter_start_date"
                      type="date"
                      value={contractorFilters.startDate}
                      onChange={(e) => setContractorFilters({ ...contractorFilters, startDate: e.target.value })}
                      className="mt-1 bg-white w-40"
                    />
                  </div>
                  <div>
                    <Label htmlFor="contractor_filter_end_date" className="text-sm">請求日（終了）</Label>
                    <Input
                      id="contractor_filter_end_date"
                      type="date"
                      value={contractorFilters.endDate}
                      onChange={(e) => setContractorFilters({ ...contractorFilters, endDate: e.target.value })}
                      className="mt-1 bg-white w-40"
                    />
                  </div>
                  <div>
                    <Label className="text-sm">委託先（複数選択可）</Label>
                    <div className="mt-2 space-y-2 max-h-40 overflow-y-auto border border-gray-200 rounded-md p-3 bg-white">
                      {contractors.map((contractor) => (
                        <div key={contractor.contractor_id} className="flex items-center">
                          <input
                            type="checkbox"
                            id={`filter_contractor_${contractor.contractor_id}`}
                            checked={contractorFilters.contractorIds.includes(contractor.contractor_id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setContractorFilters({ ...contractorFilters, contractorIds: [...contractorFilters.contractorIds, contractor.contractor_id] });
                              } else {
                                setContractorFilters({ ...contractorFilters, contractorIds: contractorFilters.contractorIds.filter(id => id !== contractor.contractor_id) });
                              }
                            }}
                            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <label htmlFor={`filter_contractor_${contractor.contractor_id}`} className="ml-2 text-sm text-gray-700 cursor-pointer">
                            {contractor.name}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                {(contractorFilters.startDate || contractorFilters.endDate || contractorFilters.contractorIds.length > 0) && (
                  <div className="mt-3 flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setContractorFilters({ startDate: '', endDate: '', contractorIds: [] })}
                    >
                      検索条件クリア
                    </Button>
                  </div>
                )}
                </>
                )}
              </CardContent>
            </Card>

            {contractorInvoices.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <p className="text-gray-500">委託先請求書がありません</p>
                <p className="text-sm text-gray-400 mt-2">「新規作成」から作成してください</p>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                {contractorInvoices
                  .filter((invoice) => {
                    // 委託先フィルター（複数選択）
                    if (contractorFilters.contractorIds.length > 0 && !contractorFilters.contractorIds.includes(invoice.contractor_id)) {
                      return false;
                    }
                    // 請求日フィルター（開始日）
                    if (contractorFilters.startDate && invoice.invoice_date && invoice.invoice_date < contractorFilters.startDate) {
                      return false;
                    }
                    // 請求日フィルター（終了日）
                    if (contractorFilters.endDate && invoice.invoice_date && invoice.invoice_date > contractorFilters.endDate) {
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
                        className={`p-4 ${index !== contractorInvoices.length - 1 ? 'border-b border-gray-100' : ''}`}
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1">
                            <div className="font-medium text-gray-900 text-lg mb-1">
                              {invoice.contractor_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              請求日: {invoice.invoice_date || '未設定'}
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
                              setSelectedContractorInvoice(invoice);
                              setShowContractorDetailDialog(true);
                            }}
                            className="flex-1 h-10 text-white bg-gray-600 hover:bg-gray-700 border-0"
                          >
                            📋 明細
                          </Button>
                          <Button 
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadContractorPDF(invoice.id);
                            }}
                            className="flex-1 h-10 font-medium bg-blue-600 hover:bg-blue-700 text-white"
                          >
                            📄 請求書PDF
                          </Button>
                          <Button 
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadContractorReceiptPDF(invoice.id);
                            }}
                            className="flex-1 h-10 font-medium bg-green-600 hover:bg-green-700 text-white"
                          >
                            🧾 領収書PDF
                          </Button>

                          <Button 
                            size="sm"
                            variant="destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedContractorInvoice(invoice);
                              setShowContractorDeleteDialog(true);
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
                      <SelectTrigger className="bg-white">
                        <SelectValue placeholder="委託先を選択" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        {contractors.map((c) => (
                          <SelectItem key={c.contractor_id} value={c.contractor_id.toString()}>
                            {c.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label>税率</Label>
                    <Select
                      value={contractorFormData.tax_rate_id.toString()}
                      onValueChange={(value) => setContractorFormData({ ...contractorFormData, tax_rate_id: parseInt(value) })}
                    >
                      <SelectTrigger className="bg-white">
                        <SelectValue placeholder="税率を選択" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        {taxRates.map((rate) => (
                          <SelectItem key={rate.tax_rate_id} value={rate.tax_rate_id.toString()}>
                            {rate.display_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label>請求日</Label>
                    <Input
                      type="date"
                      value={contractorFormData.invoice_date}
                      onChange={(e) => setContractorFormData({ ...contractorFormData, invoice_date: e.target.value })}
                      className="w-40 mt-1 bg-white"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label>領収日</Label>
                    <Input
                      type="date"
                      value={contractorFormData.receipt_date || ''}
                      onChange={(e) => setContractorFormData({ ...contractorFormData, receipt_date: e.target.value })}
                      className="w-40 mt-1 bg-white"
                    />
                  </div>
                  
                  <div>
                    <Label>商品明細</Label>
                    <div className="space-y-3 mt-2">
                      {contractorFormData.details.map((detail, index) => {
                        const selectedProduct = products.find(p => p.product_id === detail.product_id);
                        return (
                          <div key={index} className="p-4 bg-gray-50 rounded-lg">
                            <div className="flex gap-3 items-end">
                              <div className="flex-1 space-y-2">
                                <Label>商品名 *</Label>
                                <Select
                                  value={detail.product_id.toString()}
                                  onValueChange={(value) => updateDetailRow(index, 'product_id', parseInt(value))}
                                >
                                  <SelectTrigger className="bg-white border-gray-300">
                                    <SelectValue placeholder="商品を選択" />
                                  </SelectTrigger>
                                  <SelectContent className="bg-white">
                                    {products.map((p) => (
                                      <SelectItem key={p.product_id} value={p.product_id.toString()}>
                                        {p.name}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                              <div className="w-24 space-y-2">
                                <Label>数量 *</Label>
                                <Input
                                  type="number"
                                  min="1"
                                  placeholder="0"
                                  value={detail.total_quantity}
                                  onChange={(e) => updateDetailRow(index, 'total_quantity', parseInt(e.target.value) || 0)}
                                  className="bg-white border-gray-300"
                                />
                              </div>
                              <Button
                                type="button"
                                size="sm"
                                onClick={() => removeDetailRow(index)}
                                className="bg-red-600 hover:bg-red-700 text-white"
                                disabled={contractorFormData.details.length === 1}
                              >
                                削除
                              </Button>
                            </div>
                            {selectedProduct && (
                              <p className="text-xs text-gray-600 mt-2">単価: ¥{selectedProduct.price.toLocaleString()}</p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                    <Button
                      type="button"
                      onClick={addDetailRow}
                      className="w-full mt-3 bg-blue-600 hover:bg-blue-700 text-white font-medium"
                    >
                      + 明細追加
                    </Button>
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
                    disabled={generating || !contractorFormData.contractor_id || !contractorFormData.invoice_date || contractorFormData.details.length === 0}
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
              <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-2xl font-bold">委託先請求書明細</DialogTitle>
                </DialogHeader>
                {selectedContractorInvoice && (
                  <div className="space-y-6">
                    {/* 基本情報セクション */}
                    <div className="bg-gray-50 p-5 rounded-lg">
                      <h3 className="font-semibold text-lg text-gray-700 mb-4 pb-2 border-b">基本情報</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6">
                        <div className="flex items-center">
                          <span className="text-base text-gray-600 w-32">委託先</span>
                          <span className="text-base font-medium text-gray-900">{selectedContractorInvoice.contractor_name}</span>
                        </div>
                        <div className="flex items-center">
                          <span className="text-base text-gray-600 w-32">割引率</span>
                          <span className="text-base font-medium text-gray-900">{((selectedContractorInvoice.discount_rate || 0) * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex items-center">
                          <span className="text-base text-gray-600 w-32">請求日</span>
                          <span className="text-base font-medium text-gray-900">{selectedContractorInvoice.invoice_date || '-'}</span>
                        </div>
                        <div className="flex items-center">
                          <span className="text-base text-gray-600 w-32">領収日</span>
                          <span className="text-base font-medium text-gray-900">{selectedContractorInvoice.receipt_date || '-'}</span>
                        </div>
                      </div>
                      {selectedContractorInvoice.note && (
                        <div className="mt-4 pt-4 border-t">
                          <div className="flex items-start">
                            <span className="text-base text-gray-600 w-32 flex-shrink-0">但（ただし書き）</span>
                            <span className="text-base font-medium text-gray-900">{selectedContractorInvoice.note}</span>
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
                            {(selectedContractorInvoice.details || []).map((detail, index) => (
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
                              ¥{(selectedContractorInvoice.quota_subtotal || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1">
                            <span className="text-sm text-blue-900 font-medium">ノルマ対象割引額</span>
                            <span className="text-xl font-bold text-red-600">
                              -¥{(selectedContractorInvoice.quota_discount_amount || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1 border-t border-blue-300 pt-2 mt-1">
                            <span className="text-sm text-blue-900 font-semibold">ノルマ対象合計</span>
                            <span className="text-xl font-bold text-blue-900">
                              ¥{(selectedContractorInvoice.quota_total || 0).toLocaleString()}
                            </span>
                          </div>
                        </div>
                        
                        {/* ノルマ対象外（緑系） */}
                        <div className="bg-green-100 p-3 rounded-lg border-l-4 border-green-500">
                          <div className="flex justify-between items-center py-1">
                            <span className="text-sm text-green-900 font-medium">ノルマ対象外小計</span>
                            <span className="text-xl font-bold text-green-900">
                              ¥{(selectedContractorInvoice.non_quota_subtotal || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1">
                            <span className="text-sm text-green-900 font-medium">ノルマ対象外割引額</span>
                            <span className="text-xl font-bold text-red-600">
                              -¥{(selectedContractorInvoice.non_quota_discount_amount || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1 border-t border-green-300 pt-2 mt-1">
                            <span className="text-sm text-green-900 font-semibold">ノルマ対象外合計</span>
                            <span className="text-xl font-bold text-green-900">
                              ¥{(selectedContractorInvoice.non_quota_total || 0).toLocaleString()}
                            </span>
                          </div>
                        </div>
                        
                        {/* 割引対象外（オレンジ系） */}
                        <div className="bg-orange-100 p-3 rounded-lg border-l-4 border-orange-500">
                          <div className="flex justify-between items-center py-1">
                            <span className="text-sm text-orange-900 font-semibold">割引対象外金額</span>
                            <span className="text-xl font-bold text-orange-900">
                              ¥{(selectedContractorInvoice.non_discountable_amount || 0).toLocaleString()}
                            </span>
                          </div>
                        </div>
                        
                        {/* 合計（グレー系） */}
                        <div className="bg-gray-200 p-3 rounded-lg border border-gray-400 mt-4">
                          <div className="flex justify-between items-center py-1">
                            <span className="text-sm text-gray-700 font-medium">税抜合計</span>
                            <span className="text-xl font-bold text-gray-900">
                              ¥{(selectedContractorInvoice.total_amount_ex_tax || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1">
                            <span className="text-sm text-gray-700 font-medium">消費税（10%）</span>
                            <span className="text-xl font-bold text-gray-700">
                              ¥{(selectedContractorInvoice.tax_amount || 0).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-2 border-t-2 border-gray-500 pt-3 mt-2">
                            <span className="text-base text-gray-800 font-bold">税込合計</span>
                            <span className="text-2xl font-bold text-blue-600">
                              ¥{(selectedContractorInvoice.total_amount_inc_tax || 0).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* ボタンエリア */}
                    <div className="flex gap-3 justify-end pt-4 border-t">
                      <Button
                        onClick={handleEditContractorInvoice}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6"
                      >
                        編集
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowContractorDetailDialog(false);
                          setSelectedContractorInvoice(null);
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

            {/* 委託先請求書編集ダイアログ */}
            <Dialog open={showContractorEditDialog} onOpenChange={setShowContractorEditDialog}>
              <DialogContent className="w-[95vw] max-w-4xl max-h-[85vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>委託先請求書編集</DialogTitle>
                </DialogHeader>
                {editingContractorInvoice && selectedContractorInvoice && (
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <h3 className="font-semibold text-sm text-gray-700 border-b pb-2">基本情報</h3>
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="contractor">委託先</Label>
                          <Select 
                            value={editingContractorInvoice.contractor_id?.toString() || selectedContractorInvoice.contractor_id.toString()} 
                            onValueChange={(v) => setEditingContractorInvoice({...editingContractorInvoice, contractor_id: parseInt(v)})}
                          >
                            <SelectTrigger id="contractor" className="mt-1">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-white">
                              {contractors.map(c => <SelectItem key={c.contractor_id} value={c.contractor_id.toString()}>{c.name}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label htmlFor="invoice_date">請求日</Label>
                          <Input 
                            id="invoice_date"
                            type="date" 
                            className="w-40 mt-1"
                            value={editingContractorInvoice.invoice_date || selectedContractorInvoice.invoice_date || ''} 
                            onChange={(e) => setEditingContractorInvoice({...editingContractorInvoice, invoice_date: e.target.value})} 
                          />
                        </div>
                        <div>
                          <Label htmlFor="receipt_date">領収日</Label>
                          <Input 
                            id="receipt_date"
                            type="date" 
                            className="w-40 mt-1"
                            value={editingContractorInvoice.receipt_date || selectedContractorInvoice.receipt_date || ''} 
                            onChange={(e) => setEditingContractorInvoice({...editingContractorInvoice, receipt_date: e.target.value})} 
                          />
                        </div>
                        <div>
                          <Label>割引率</Label>
                          <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md">
                            <p className="text-sm text-gray-700">現在の割引率: <span className="font-bold">{((selectedContractorInvoice.discount_rate || 0) * 100).toFixed(0)}%</span></p>
                            <p className="text-xs text-gray-500 mt-1">※割引率は合計金額から自動設定されます</p>
                          </div>
                        </div>
                        <div>
                          <Label htmlFor="note">但（ただし書き）</Label>
                          <Input 
                            id="note"
                            className="mt-1"
                            value={editingContractorInvoice.note || ''} 
                            onChange={(e) => setEditingContractorInvoice({...editingContractorInvoice, note: e.target.value})} 
                            placeholder="商品代として"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <h3 className="font-semibold text-sm text-gray-700 border-b pb-2">商品明細</h3>
                      <div className="space-y-2">
                        {(editingContractorInvoice.details || selectedContractorInvoice.details).map((detail: any, index: number) => {
                          const product = products.find(p => p.product_id === (detail.product_id || selectedContractorInvoice.details[index]?.product_id));
                          const isNewItem = editingContractorInvoice.details && !selectedContractorInvoice.details.find((d: any) => d.product_id === detail.product_id);
                          
                          return (
                            <div key={index} className="bg-gray-50 p-3 rounded border border-gray-200">
                              <div className="space-y-3">
                                <div>
                                  {isNewItem || !detail.product_id ? (
                                    <div>
                                      <Label htmlFor={`product_${index}`} className="text-xs">商品名</Label>
                                      <Select 
                                        value={detail.product_id?.toString() || ''} 
                                        onValueChange={(v) => {
                                          const selectedProduct = products.find(p => p.product_id === parseInt(v));
                                          const updatedDetails = [...(editingContractorInvoice.details || selectedContractorInvoice.details)];
                                          updatedDetails[index] = { 
                                            ...updatedDetails[index], 
                                            product_id: parseInt(v),
                                            unit_price: selectedProduct ? selectedProduct.price : updatedDetails[index].unit_price
                                          };
                                          setEditingContractorInvoice({ ...editingContractorInvoice, details: updatedDetails });
                                        }}
                                      >
                                        <SelectTrigger id={`product_${index}`} className="mt-1">
                                          <SelectValue placeholder="商品を選択" />
                                        </SelectTrigger>
                                        <SelectContent className="bg-white">
                                          {products.map(p => (
                                            <SelectItem key={p.product_id} value={p.product_id.toString()}>
                                              {p.name}
                                            </SelectItem>
                                          ))}
                                        </SelectContent>
                                      </Select>
                                    </div>
                                  ) : (
                                    <div>
                                      <p className="text-xs text-gray-500 mb-1">商品名</p>
                                      <p className="font-medium text-sm">{product?.name || '不明な商品'}</p>
                                    </div>
                                  )}
                                </div>
                                <div className="flex items-end justify-between gap-3">
                                  <div className="flex-1 max-w-xs">
                                    <Label htmlFor={`quantity_${index}`} className="text-xs">数量</Label>
                                    <Input 
                                      id={`quantity_${index}`}
                                      type="number" 
                                      className="mt-1"
                                      value={(editingContractorInvoice.details && editingContractorInvoice.details[index]?.total_quantity) || detail.total_quantity || 0} 
                                      onChange={(e) => {
                                        const updatedDetails = [...(editingContractorInvoice.details || selectedContractorInvoice.details)];
                                        updatedDetails[index] = { ...updatedDetails[index], total_quantity: parseInt(e.target.value) || 0 };
                                        setEditingContractorInvoice({ ...editingContractorInvoice, details: updatedDetails });
                                      }} 
                                      min="0"
                                    />
                                  </div>
                                  <Button 
                                    size="sm" 
                                    onClick={() => {
                                      const updatedDetails = [...(editingContractorInvoice.details || selectedContractorInvoice.details)];
                                      updatedDetails.splice(index, 1);
                                      setEditingContractorInvoice({ ...editingContractorInvoice, details: updatedDetails });
                                    }}
                                    className="bg-red-600 hover:bg-red-700 text-white"
                                    disabled={(editingContractorInvoice.details || selectedContractorInvoice.details).length === 1}
                                  >
                                    削除
                                  </Button>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      
                      <div className="flex justify-between items-center pt-3">
                        <Button 
                          onClick={() => {
                            const updatedDetails = [...(editingContractorInvoice.details || selectedContractorInvoice.details), { product_id: 0, total_quantity: 1, unit_price: 0 }];
                            setEditingContractorInvoice({ ...editingContractorInvoice, details: updatedDetails });
                          }} 
                          size="sm" 
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          + 明細追加
                        </Button>
                      </div>
                    </div>

                    <div className="flex gap-2 justify-end pt-4 border-t">
                      <Button 
                        onClick={handleSaveContractorEdit} 
                        disabled={generating}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {generating ? '保存中...' : '保存'}
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => setShowContractorEditDialog(false)}
                        disabled={generating}
                        className="px-6"
                      >
                        キャンセル
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
