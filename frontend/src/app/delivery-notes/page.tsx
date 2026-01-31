'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useDropzone } from 'react-dropzone';
import { Upload, FileImage, X } from 'lucide-react';

interface DeliveryNote {
  id: number;
  sales_person_id: number;
  tax_rate_id: number;
  delivery_date: string;
  billing_date: string;
  delivery_note_number: string;
  remarks?: string;
  details: DeliveryNoteDetail[];
}

interface DeliveryNoteDetail {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  remarks?: string;
}

interface SalesPerson {
  id: number;
  name: string;
}

interface Product {
  id: number;
  name: string;
  price: number;
}

interface Contractor {
  id: number;
  name: string;
}

interface RecognitionResult {
  success: boolean;
  salesPersonId?: number | string;
  deliveryDate?: string;
  billingDate?: string;
  taxRateId?: number | string;
  details?: Array<{
    productId: number | string;
    quantity: number;
    unitPrice: number;
  }>;
  // 一部コードで API からの解析結果を `parsedData` として扱うための互換プロパティ
  parsedData?: {
    salesPersonId?: number | string;
    deliveryDate?: string;
    products?: Array<{
      productId: number | string;
      quantity: number;
      unitPrice: number;
    }>;
  };
  failureReason?: string;
}

interface UploadedImage {
  file: File;
  preview: string;
  recognitionResult?: RecognitionResult;
  base64Data?: string;
  fileName?: string;
  fileType?: string;
  isDuplicate?: boolean;
  duplicateInfo?: {
    recognizedAt: string;
    success: boolean;
  };
}

export default function DeliveryNotesPage() {
  const [deliveryNotes, setDeliveryNotes] = useState<DeliveryNote[]>([]);
  const [salesPersons, setSalesPersons] = useState<SalesPerson[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [contractors, setContractors] = useState<Contractor[]>([]);
  const [activeTab, setActiveTab] = useState<'list' | 'manual' | 'recognition'>('list');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedNote, setSelectedNote] = useState<DeliveryNote | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingNote, setEditingNote] = useState<any>(null);
  const [uploadedImages, setUploadedImages] = useState<UploadedImage[]>([]);
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    salesPersonIds: [] as string[]
  });
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [newDeliveryNote, setNewDeliveryNote] = useState({
    sales_person_id: '',
    tax_rate_id: '1', // Default tax rate
    delivery_date: '',
    billing_date: '',
    remarks: '',
    details: [{ product_id: '', quantity: '' }]
  });
  const router = useRouter();

  // Client-only date formatter to avoid SSR/CSR hydration mismatch.
  const ClientDate = ({ value }: { value: string | undefined | null }) => {
    const [display, setDisplay] = useState<string | null>(value ?? null);
    useEffect(() => {
      if (!value) return;
      try {
        const d = new Date(value);
        // If invalid date, keep original
        if (!isNaN(d.getTime())) {
          setDisplay(d.toLocaleDateString());
        }
      } catch {
        // ignore
      }
    }, [value]);
    return <>{display ?? '-'}</>;
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadData();
    
    // localStorageから画像認識状態を復元
    const savedImages = localStorage.getItem('uploadedImages_recognition');
    if (savedImages) {
      try {
        const parsedImages = JSON.parse(savedImages);
        const restoredImages = parsedImages.map((img: any) => {
          // Base64からFileオブジェクトを再構築
          const byteString = atob(img.base64Data.split(',')[1]);
          const mimeString = img.base64Data.split(',')[0].split(':')[1].split(';')[0];
          const ab = new ArrayBuffer(byteString.length);
          const ia = new Uint8Array(ab);
          for (let i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i);
          }
          const blob = new Blob([ab], { type: mimeString });
          const file = new File([blob], img.fileName || 'image.jpg', { type: mimeString });
          
          return {
            file,
            preview: URL.createObjectURL(blob),
            recognitionResult: img.recognitionResult,
            base64Data: img.base64Data,
            fileName: img.fileName,
            fileType: img.fileType
          };
        });
        setUploadedImages(restoredImages);
        
        // 未認識の画像があれば自動的に認識処理を再開
        const unrecognizedImages = restoredImages.filter((img: UploadedImage) => !img.recognitionResult);
        if (unrecognizedImages.length > 0) {
          console.log(`${unrecognizedImages.length}件の未認識画像を検出。認識処理を再開します。`);
          // 非同期で認識処理を実行
          (async () => {
            for (const image of unrecognizedImages) {
              await recognizeImage(image);
            }
          })();
        }
      } catch (error) {
        console.error('Failed to restore images from localStorage:', error);
        localStorage.removeItem('uploadedImages_recognition');
      }
    }
  }, [router]);

  // DB内の納品書データと比較して重複をチェック
  const checkDuplicateInDeliveryNotes = (result: RecognitionResult): boolean => {
    if (!result.success || !result.parsedData) return false;
    
    const { salesPersonId, deliveryDate, products } = result.parsedData;

    // 納品書一覧から同一のデータを検索
    const salesPersonIdNum = salesPersonId ? (typeof salesPersonId === 'number' ? salesPersonId : parseInt(salesPersonId, 10)) : undefined;
    if (!salesPersonIdNum || !deliveryDate || !products) return false;

    return deliveryNotes.some(note => {
      // 販売員IDと納品日が一致するかチェック
      if (note.sales_person_id !== salesPersonIdNum) return false;
      if (note.delivery_date !== deliveryDate) return false;

      // 商品明細の数が一致するかチェック
      if (note.details.length !== products.length) return false;
      
      // すべての商品明細が一致するかチェック
      return products.every((product: any) => {
        return note.details.some(detail => 
          detail.product_id === product.productId &&
          detail.quantity === product.quantity &&
          detail.unit_price === product.unitPrice
        );
      });
    });
  };

  const loadData = async () => {
    try {
      const [deliveryNotesRes, salesPersonsRes, productsRes, contractorsRes] = await Promise.all([
        apiClient.getDeliveryNotes(),
        apiClient.getSalesPersons(),
        apiClient.getProducts(),
        apiClient.getContractors(),
      ]);

      if (deliveryNotesRes.data) setDeliveryNotes(deliveryNotesRes.data as DeliveryNote[]);
      if (salesPersonsRes.data) setSalesPersons(salesPersonsRes.data as SalesPerson[]);
      if (productsRes.data) setProducts(productsRes.data as Product[]);
      if (contractorsRes.data) setContractors(contractorsRes.data as Contractor[]);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  // Image recognition functions
  const onDrop = async (acceptedFiles: File[]) => {
    const newImages: UploadedImage[] = await Promise.all(
      acceptedFiles.map(async (file) => {
        // FileをBase64に変換
        const base64Data = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.readAsDataURL(file);
        });
        
        return {
          file,
          preview: URL.createObjectURL(file),
          base64Data,
          fileName: file.name,
          fileType: file.type,
          isDuplicate: false,
          duplicateInfo: undefined
        };
      })
    );
    
    const updatedImages = [...uploadedImages, ...newImages];
    setUploadedImages(updatedImages);
    saveImagesToLocalStorage(updatedImages);
    
    // Process each image
    for (const image of newImages) {
      await recognizeImage(image);
    }
  };

  const recognizeImage = async (image: UploadedImage) => {
    setIsRecognizing(true);
    try {
      const result = await apiClient.recognizeImage(image.file);
      console.log('🔍 認識API レスポンス:', result);
      
      if (result.data) {
        image.recognitionResult = (result.data as any).recognition_result;
        console.log('✅ 認識結果:', image.recognitionResult);
        console.log('📊 salesPersonId:', image.recognitionResult?.salesPersonId, 'typeof:', typeof image.recognitionResult?.salesPersonId);
        
        // DB内の納品書と照合して重複チェック
        if (image.recognitionResult?.success) {
          const isDuplicateInDB = checkDuplicateInDeliveryNotes(image.recognitionResult);
          if (isDuplicateInDB) {
            image.isDuplicate = true;
            image.duplicateInfo = {
              recognizedAt: new Date().toISOString(),
              success: true
            };
          }
        }
        
        // 認識履歴に追加
        saveRecognitionHistory({
          fileName: image.fileName || 'unknown',
          imageHash: image.base64Data?.substring(0, 100) || '',
          recognizedAt: new Date().toISOString(),
          success: image.recognitionResult?.success || false
        });
        
        setUploadedImages(prev => {
          const updated = [...prev];
          saveImagesToLocalStorage(updated);
          return updated;
        }); // Trigger re-render
      }
    } catch (error) {
      console.error('Recognition failed:', error);
      image.recognitionResult = { success: false, failureReason: '認識に失敗しました' };
      
      // 失敗も履歴に追加
      saveRecognitionHistory({
        fileName: image.fileName || 'unknown',
        imageHash: image.base64Data?.substring(0, 100) || '',
        recognizedAt: new Date().toISOString(),
        success: false
      });
      
      setUploadedImages(prev => {
        const updated = [...prev];
        saveImagesToLocalStorage(updated);
        return updated;
      });
    } finally {
      setIsRecognizing(false);
    }
  };

  const removeImage = (index: number) => {
    setUploadedImages(prev => {
      const newImages = [...prev];
      URL.revokeObjectURL(newImages[index].preview);
      newImages.splice(index, 1);
      saveImagesToLocalStorage(newImages);
      return newImages;
    });
  };
  
  // localStorageに画像データを保存
  const saveImagesToLocalStorage = (images: UploadedImage[]) => {
    try {
      const dataToSave = images.map(img => ({
        base64Data: img.base64Data,
        fileName: img.fileName,
        fileType: img.fileType,
        recognitionResult: img.recognitionResult
      }));
      localStorage.setItem('uploadedImages_recognition', JSON.stringify(dataToSave));
    } catch (error) {
      console.error('Failed to save images to localStorage:', error);
    }
  };
  
  // 認識履歴の管理
  interface RecognitionHistoryItem {
    fileName: string;
    imageHash: string;
    recognizedAt: string;
    success: boolean;
  }
  
  const getRecognitionHistory = (): RecognitionHistoryItem[] => {
    try {
      const history = localStorage.getItem('recognition_history');
      return history ? JSON.parse(history) : [];
    } catch (error) {
      console.error('Failed to load recognition history:', error);
      return [];
    }
  };
  
  const saveRecognitionHistory = (item: RecognitionHistoryItem) => {
    try {
      const history = getRecognitionHistory();
      // 同じファイルの古い履歴は削除
      const filteredHistory = history.filter(
        h => h.fileName !== item.fileName && h.imageHash !== item.imageHash
      );
      // 新しい履歴を追加（最大100件まで保持）
      const updatedHistory = [item, ...filteredHistory].slice(0, 100);
      localStorage.setItem('recognition_history', JSON.stringify(updatedHistory));
    } catch (error) {
      console.error('Failed to save recognition history:', error);
    }
  };

  const useRecognitionResult = async (result: RecognitionResult) => {
    if (!result.success || !result.salesPersonId || !result.deliveryDate || !result.taxRateId) {
      alert('認識結果が不完全です');
      return;
    }

    try {
      // 請求日を計算（20日締め）
      const deliveryDate = new Date(result.deliveryDate);
      const day = deliveryDate.getDate();
      let billingDate: Date;
      
      if (day <= 20) {
        // 1-20日 → 当月20日
        billingDate = new Date(deliveryDate.getFullYear(), deliveryDate.getMonth(), 20);
      } else {
        // 21-31日 → 翌月20日
        billingDate = new Date(deliveryDate.getFullYear(), deliveryDate.getMonth() + 1, 20);
      }

      // フォーマット: YYYY-MM-DD
      const formatDate = (date: Date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      // 納品書番号を生成
      const deliveryNoteNumber = `DN-${Date.now()}`;

      // 明細データを整形
      const details = result.details?.map(d => ({
        product_id: typeof d.productId === 'number' ? d.productId : parseInt(d.productId),
        quantity: parseInt(d.quantity.toString()),
        unit_price: parseInt(d.unitPrice.toString()),
        remarks: ''
      })) || [];

      // DBに直接登録
      const response = await apiClient.createDeliveryNote({
        sales_person_id: typeof result.salesPersonId === 'number' ? result.salesPersonId : parseInt(result.salesPersonId),
        tax_rate_id: typeof result.taxRateId === 'number' ? result.taxRateId : parseInt(result.taxRateId),
        delivery_date: result.deliveryDate,
        billing_date: formatDate(billingDate),
        delivery_note_number: deliveryNoteNumber,
        remarks: '画像認識から登録',
        details
      });

      if (response?.data) {
        alert('納品書を登録しました');
        loadData(); // 納品書一覧を更新
        // 画像をクリア（登録済み）
        setUploadedImages(prev => {
          const filtered = prev.filter(img => img.recognitionResult !== result);
          saveImagesToLocalStorage(filtered);
          return filtered;
        });
      } else {
        throw new Error(response?.error || '登録に失敗しました');
      }
    } catch (error: any) {
      console.error('Failed to create delivery note:', error);
      alert(`登録に失敗しました: ${error.message || '不明なエラー'}`);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png']
    },
    multiple: true
  });

  const handleCreate = async () => {
    try {
      // バリデーション
      if (!newDeliveryNote.sales_person_id) {
        alert('販売員を選択してください');
        return;
      }
      if (!newDeliveryNote.delivery_date) {
        alert('納品日を入力してください');
        return;
      }
      if (!newDeliveryNote.billing_date) {
        alert('請求日が設定されていません。納品日を入力してください');
        return;
      }
      if (newDeliveryNote.details.length === 0) {
        alert('商品明細を追加してください');
        return;
      }
      
      // 明細のバリデーション
      for (let i = 0; i < newDeliveryNote.details.length; i++) {
        const detail = newDeliveryNote.details[i];
        if (!detail.product_id) {
          alert(`明細${i + 1}: 商品名を選択してください`);
          return;
        }
        if (!detail.quantity || parseInt(detail.quantity) <= 0) {
          alert(`明細${i + 1}: 数量を入力してください`);
          return;
        }
      }

      // UUIDを生成
      const deliveryNoteNumber = `DN-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      // 商品マスタから単価を取得して明細を作成
      const details = newDeliveryNote.details.map(detail => {
        const product = products.find(p => p.id.toString() === detail.product_id);
        return {
          product_id: parseInt(detail.product_id),
          quantity: parseInt(detail.quantity),
          unit_price: product?.price || 0, // 商品マスタから単価を自動設定
          remarks: (detail as any).remarks || ''
        };
      });

      const result = await apiClient.createDeliveryNote({
        sales_person_id: parseInt(newDeliveryNote.sales_person_id),
        tax_rate_id: parseInt(newDeliveryNote.tax_rate_id),
        delivery_date: newDeliveryNote.delivery_date,
        billing_date: newDeliveryNote.billing_date,
        delivery_note_number: deliveryNoteNumber,
        remarks: newDeliveryNote.remarks,
        details
      });

      if (result?.data) {
        alert('納品書を作成しました');
        setIsDialogOpen(false);
        setNewDeliveryNote({
          sales_person_id: '',
          tax_rate_id: '1',
          delivery_date: '',
          billing_date: '',
          remarks: '',
          details: [{ product_id: '', quantity: '' }]
        });
        loadData();
      } else {
        throw new Error(result?.error || '作成に失敗しました');
      }
    } catch (error: any) {
      console.error('Failed to create delivery note:', error);
      alert(`作成に失敗しました: ${error.message || '不明なエラー'}`);
    }
  };

  const addDetail = () => {
    setNewDeliveryNote({
      ...newDeliveryNote,
      details: [...newDeliveryNote.details, { product_id: '', quantity: '' }]
    });
  };

  const removeDetail = (index: number) => {
    const updatedDetails = [...newDeliveryNote.details];
    updatedDetails.splice(index, 1);
    setNewDeliveryNote({ ...newDeliveryNote, details: updatedDetails });
  };

  const handleDeleteNote = async () => {
    if (!selectedNote) return;
    
    try {
      console.log('Deleting delivery note:', selectedNote.id);
      const response = await apiClient.deleteDeliveryNote(selectedNote.id);
      console.log('Delete response:', response);
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      setShowDeleteDialog(false);
      setIsDialogOpen(false);
      setSelectedNote(null);
      alert('納品書を削除しました');
      loadData();
    } catch (error: any) {
      console.error('Failed to delete delivery note:', error);
      const errorMsg = error.message || '削除に失敗しました';
      alert(`削除に失敗しました: ${errorMsg}`);
    }
  };

  const handleEditNote = () => {
    if (!selectedNote) return;
    setEditingNote({
      sales_person_id: selectedNote.sales_person_id.toString(),
      tax_rate_id: selectedNote.tax_rate_id.toString(),
      delivery_date: selectedNote.delivery_date,
      billing_date: selectedNote.billing_date,
      delivery_note_number: selectedNote.delivery_note_number,
      remarks: selectedNote.remarks || '',
      details: selectedNote.details.map(d => ({
        product_id: d.product_id.toString(),
        quantity: d.quantity.toString(),
        unit_price: d.unit_price.toString(),
        remarks: d.remarks || ''
      }))
    });
    setIsDialogOpen(false);
    setShowEditDialog(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedNote || !editingNote) return;

    try {
      // 明細のバリデーションと単価の自動設定
      const details = editingNote.details.map((d: any) => {
        const product = products.find(p => p.id === parseInt(d.product_id));
        const unitPrice = d.unit_price ? parseInt(d.unit_price) : (product?.price || 0);
        
        return {
          product_id: parseInt(d.product_id),
          quantity: parseInt(d.quantity),
          unit_price: unitPrice,
          remarks: d.remarks || ''
        };
      });

      const updateData = {
        sales_person_id: parseInt(editingNote.sales_person_id),
        tax_rate_id: parseInt(editingNote.tax_rate_id),
        delivery_date: editingNote.delivery_date,
        billing_date: editingNote.billing_date,
        delivery_note_number: editingNote.delivery_note_number,
        remarks: editingNote.remarks,
        details
      };

      console.log('Updating delivery note:', { id: selectedNote.id, ...updateData });

      const response = await apiClient.updateDeliveryNote(selectedNote.id, updateData);

      console.log('Update response:', response);

      setShowEditDialog(false);
      setEditingNote(null);
      setSelectedNote(null);
      alert('納品書を更新しました');
      loadData();
    } catch (error: any) {
      console.error('Failed to update delivery note:', error);
      console.error('Error details:', error.response?.data);
      const errorMsg = error.response?.data?.detail || error.message || '不明なエラー';
      alert(`更新に失敗しました: ${errorMsg}`);
    }
  };

  const addEditDetail = () => {
    setEditingNote({
      ...editingNote,
      details: [...editingNote.details, { product_id: '', quantity: '', unit_price: '', remarks: '' }]
    });
  };

  const removeEditDetail = (index: number) => {
    const updatedDetails = [...editingNote.details];
    updatedDetails.splice(index, 1);
    setEditingNote({ ...editingNote, details: updatedDetails });
  };

  const updateEditDetail = (index: number, field: string, value: string) => {
    const updatedDetails = [...editingNote.details];
    updatedDetails[index] = { ...updatedDetails[index], [field]: value };
    setEditingNote({ ...editingNote, details: updatedDetails });
  };

  const updateDetail = (index: number, field: string, value: string) => {
    const updatedDetails = [...newDeliveryNote.details];
    updatedDetails[index] = { ...updatedDetails[index], [field]: value };
    setNewDeliveryNote({ ...newDeliveryNote, details: updatedDetails });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto pt-4 pb-6 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('list')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'list'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                一覧
              </button>
              <button
                onClick={() => setActiveTab('manual')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'manual'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                手動作成
              </button>
              <button
                onClick={() => setActiveTab('recognition')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'recognition'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                画像認識
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'list' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">納品書一覧</h2>
              </div>
              
              {/* フィルター */}
              <Card className="mb-6">
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
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="filter_start_date" className="text-sm">納品日（開始）</Label>
                      <Input
                        id="filter_start_date"
                        type="date"
                        value={filters.startDate}
                        onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                        className="mt-1 bg-white w-40"
                      />
                    </div>
                    <div>
                      <Label htmlFor="filter_end_date" className="text-sm">納品日（終了）</Label>
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
                              id={`sales_person_${person.id}`}
                              checked={filters.salesPersonIds.includes(person.id.toString())}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setFilters({ ...filters, salesPersonIds: [...filters.salesPersonIds, person.id.toString()] });
                                } else {
                                  setFilters({ ...filters, salesPersonIds: filters.salesPersonIds.filter(id => id !== person.id.toString()) });
                                }
                              }}
                              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            />
                            <label htmlFor={`sales_person_${person.id}`} className="ml-2 text-sm text-gray-700 cursor-pointer">
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
              
              {deliveryNotes.length === 0 ? (
                <Card>
                  <CardContent className="py-8 text-center text-gray-500">
                    納品書がありません
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {deliveryNotes
                    .filter((note) => {
                      // 販売員フィルター（複数選択）
                      if (filters.salesPersonIds.length > 0 && !filters.salesPersonIds.includes(note.sales_person_id.toString())) {
                        return false;
                      }
                      // 納品日フィルター（開始日）
                      if (filters.startDate && note.delivery_date < filters.startDate) {
                        return false;
                      }
                      // 納品日フィルター（終了日）
                      if (filters.endDate && note.delivery_date > filters.endDate) {
                        return false;
                      }
                      return true;
                    })
                    .sort((a, b) => {
                      // 納品日の降順でソート
                      return b.delivery_date.localeCompare(a.delivery_date);
                    })
                    .map((note) => {
                    const salesPerson = salesPersons.find(sp => sp.id === note.sales_person_id);
                    const totalAmount = note.details.reduce((sum, detail) => sum + (detail.quantity * detail.unit_price), 0);
                    const taxAmount = Math.floor(totalAmount * 0.1);
                    const totalWithTax = totalAmount + taxAmount;
                    
                    return (
                      <Card 
                        key={note.id} 
                        className="hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => { setSelectedNote(note); setIsDialogOpen(true); }}
                      >
                        <CardContent className="p-4">
                          <div className="flex justify-between items-center">
                            <div className="flex-1">
                              <p className="text-xs text-gray-500 mb-1">納品日</p>
                              <p className="font-bold text-base text-gray-900 mb-2"><ClientDate value={note.delivery_date} /></p>
                              <p className="text-xs text-gray-500">販売員</p>
                              <p className="font-medium text-sm text-gray-900">{salesPerson?.name || '-'}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-gray-500 mb-1">税込合計</p>
                              <p className="font-bold text-xl text-blue-600">¥{totalWithTax.toLocaleString()}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Delivery Note Detail Dialog */}
          <Dialog open={isDialogOpen} onOpenChange={(open) => { if (!open) setSelectedNote(null); setIsDialogOpen(open); }}>
            <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold">納品書詳細</DialogTitle>
                <DialogDescription className="text-sm text-gray-500">{selectedNote?.delivery_note_number}</DialogDescription>
              </DialogHeader>
              {selectedNote ? (
                <div className="space-y-6">
                  {/* 基本情報セクション */}
                  <div className="bg-gray-50 p-5 rounded-lg">
                    <h3 className="font-semibold text-lg text-gray-700 mb-4 pb-2 border-b">基本情報</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6">
                      <div className="flex items-center">
                        <span className="text-base text-gray-600 w-28">販売員</span>
                        <span className="text-base font-medium text-gray-900">{salesPersons.find(sp => sp.id === selectedNote.sales_person_id)?.name}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-base text-gray-600 w-28">税率</span>
                        <span className="text-base font-medium text-gray-900">10%</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-base text-gray-600 w-28">納品日</span>
                        <span className="text-base font-medium text-gray-900"><ClientDate value={selectedNote.delivery_date} /></span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-base text-gray-600 w-28">請求日</span>
                        <span className="text-base font-medium text-gray-900"><ClientDate value={selectedNote.billing_date} /></span>
                      </div>
                    </div>
                    {selectedNote.remarks && (
                      <div className="mt-4 pt-4 border-t">
                        <div className="flex items-start">
                          <span className="text-base text-gray-600 w-28 flex-shrink-0">備考</span>
                          <span className="text-base font-medium text-gray-900">{selectedNote.remarks}</span>
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
                          {selectedNote.details.map((d, index) => (
                            <TableRow 
                              key={d.id} 
                              className={`border-b border-gray-200 ${
                                index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                              }`}
                            >
                              <TableCell className="text-sm text-gray-900 py-3 px-3 font-medium">
                                {products.find(p => p.id === d.product_id)?.name || d.product_id}
                              </TableCell>
                              <TableCell className="text-center text-sm text-gray-900 py-3 px-2">
                                {d.quantity}
                              </TableCell>
                              <TableCell className="text-right text-sm text-gray-700 py-3 px-2">
                                ¥{d.unit_price.toLocaleString()}
                              </TableCell>
                              <TableCell className="text-right font-medium text-sm text-gray-900 py-3 px-2">
                                ¥{(d.quantity * d.unit_price).toLocaleString()}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>

                  {/* 合計セクション */}
                  <div className="bg-blue-50 p-5 rounded-lg border-2 border-blue-200">
                    <div className="space-y-3">
                      <div className="flex justify-between items-center py-2 border-b border-blue-200">
                        <span className="text-sm text-gray-700 font-medium">小計（税抜）</span>
                        <span className="text-xl font-bold text-gray-900">
                          ¥{selectedNote.details.reduce((s, d) => s + (d.quantity * d.unit_price), 0).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center py-2 border-b border-blue-200">
                        <span className="text-sm text-gray-700 font-medium">消費税（10%）</span>
                        <span className="text-xl font-bold text-gray-700">
                          ¥{Math.floor(selectedNote.details.reduce((s, d) => s + (d.quantity * d.unit_price), 0) * 0.1).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center py-3 bg-blue-100 -mx-5 px-5 rounded-b-lg">
                        <span className="text-base text-gray-800 font-semibold">合計（税込）</span>
                        <span className="text-2xl font-bold text-blue-600">
                          ¥{Math.floor(selectedNote.details.reduce((s, d) => s + (d.quantity * d.unit_price), 0) * 1.1).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* ボタンエリア */}
                  <div className="flex gap-3 justify-end pt-4 border-t">
                    <Button
                      onClick={handleEditNote}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6"
                    >
                      編集
                    </Button>
                    <Button
                      onClick={() => setShowDeleteDialog(true)}
                      className="bg-red-600 hover:bg-red-700 text-white font-medium px-6"
                    >
                      削除
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => { setIsDialogOpen(false); setSelectedNote(null); }}
                      className="px-6"
                    >
                      閉じる
                    </Button>
                  </div>
                </div>
              ) : (
                <p>納品書が選択されていません。</p>
              )}
            </DialogContent>
          </Dialog>

          {/* Edit Dialog */}
          <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
            <DialogContent className="w-[95vw] max-w-4xl max-h-[85vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>納品書編集</DialogTitle>
              </DialogHeader>
              {editingNote && (
                <div className="space-y-6">
                  <div className="space-y-4">
                    <h3 className="font-semibold text-sm text-gray-700 border-b pb-2">基本情報</h3>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="sales_person">販売員</Label>
                        <Select value={editingNote.sales_person_id} onValueChange={(v) => setEditingNote({...editingNote, sales_person_id: v})}>
                          <SelectTrigger id="sales_person" className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-white">
                            {salesPersons.map(sp => <SelectItem key={sp.id} value={sp.id.toString()}>{sp.name}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="delivery_date">納品日</Label>
                          <Input 
                            id="delivery_date"
                            type="date" 
                            className="w-40 mt-1"
                            value={editingNote.delivery_date} 
                            onChange={(e) => {
                              // 20日締めで請求日を計算
                              const deliveryDate = new Date(e.target.value);
                              const day = deliveryDate.getDate();
                              
                              let billingDate;
                              if (day <= 20) {
                                // 1日〜20日の場合：当月20日
                                billingDate = new Date(deliveryDate.getFullYear(), deliveryDate.getMonth(), 20);
                              } else {
                                // 21日〜末日の場合：翌月20日
                                billingDate = new Date(deliveryDate.getFullYear(), deliveryDate.getMonth() + 1, 20);
                              }
                              
                              setEditingNote({
                                ...editingNote, 
                                delivery_date: e.target.value,
                                billing_date: billingDate.toISOString().split('T')[0]
                              });
                            }} 
                          />
                        </div>
                        <div>
                          <Label htmlFor="billing_date">請求日（20日締め）</Label>
                          <Input 
                            id="billing_date"
                            type="date" 
                            className="w-40 mt-1 bg-gray-100"
                            value={editingNote.billing_date} 
                            readOnly
                            disabled
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="remarks">備考</Label>
                        <Input 
                          id="remarks"
                          className="mt-1"
                          value={editingNote.remarks} 
                          onChange={(e) => setEditingNote({...editingNote, remarks: e.target.value})} 
                          placeholder="備考を入力"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h3 className="font-semibold text-sm text-gray-700 border-b pb-2">商品明細</h3>
                    <div className="space-y-2">
                      {editingNote.details.map((detail: any, index: number) => {
                        const product = products.find(p => p.id === parseInt(detail.product_id));
                        const quantity = parseInt(detail.quantity) || 0;
                        const isNewItem = !selectedNote?.details.find(d => d.product_id === parseInt(detail.product_id));
                        
                        return (
                          <div key={index} className="bg-gray-50 p-3 rounded border border-gray-200">
                            <div className="space-y-3">
                              <div>
                                {isNewItem ? (
                                  <div>
                                    <Label htmlFor={`product_${index}`} className="text-xs">商品名</Label>
                                    <Select 
                                      value={detail.product_id?.toString() || ''} 
                                      onValueChange={(v) => {
                                        const selectedProduct = products.find(p => p.id === parseInt(v));
                                        const updatedDetails = [...editingNote.details];
                                        updatedDetails[index] = { 
                                          ...updatedDetails[index], 
                                          product_id: v,
                                          unit_price: selectedProduct ? selectedProduct.price.toString() : updatedDetails[index].unit_price
                                        };
                                        setEditingNote({ ...editingNote, details: updatedDetails });
                                      }}
                                    >
                                      <SelectTrigger id={`product_${index}`} className="mt-1">
                                        <SelectValue placeholder="商品を選択" />
                                      </SelectTrigger>
                                      <SelectContent className="bg-white">
                                        {products.map(p => (
                                          <SelectItem key={p.id} value={p.id.toString()}>
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
                                    value={detail.quantity} 
                                    onChange={(e) => updateEditDetail(index, 'quantity', e.target.value)} 
                                    min="0"
                                  />
                                </div>
                                <Button 
                                  size="sm" 
                                  onClick={() => removeEditDetail(index)}
                                  className="bg-red-600 hover:bg-red-700 text-white"
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
                      <Button onClick={addEditDetail} size="sm" className="bg-blue-600 hover:bg-blue-700 text-white">
                        + 明細追加
                      </Button>
                    </div>
                  </div>

                  <div className="flex gap-2 justify-end pt-4 border-t">
                    <Button 
                      onClick={handleSaveEdit} 
                      className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6"
                    >
                      保存
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => setShowEditDialog(false)}
                      className="px-6"
                    >
                      キャンセル
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>

          {/* Delete Confirmation Dialog */}
          <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
            <DialogContent className="w-[95vw] max-w-md">
              <DialogHeader>
                <DialogTitle>納品書削除</DialogTitle>
                <DialogDescription>
                  この納品書を削除してもよろしいですか？
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {selectedNote && (
                  <div className="bg-gray-50 p-3 rounded text-sm space-y-1">
                    <p><span className="font-medium">納品書番号:</span> {selectedNote.delivery_note_number}</p>
                    <p><span className="font-medium">販売員:</span> {salesPersons.find(sp => sp.id === selectedNote.sales_person_id)?.name}</p>
                  </div>
                )}
                <p className="text-sm text-red-600">この操作は取り消せません。</p>
              </div>
              <div className="flex gap-2 pt-4">
                <Button 
                  onClick={handleDeleteNote} 
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                >
                  削除
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setShowDeleteDialog(false)} 
                  className="flex-1"
                >
                  キャンセル
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          {activeTab === 'manual' && (
            <Card>
              <CardHeader>
                <CardTitle>納品書手動作成</CardTitle>
                <CardDescription>納品書を手動で作成します</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* 基本情報 */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">基本情報</h3>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="sales_person">販売員 *</Label>
                        <Select value={newDeliveryNote.sales_person_id} onValueChange={(value) => setNewDeliveryNote({ ...newDeliveryNote, sales_person_id: value })}>
                          <SelectTrigger className="w-full bg-white">
                            <SelectValue placeholder="販売員を選択" />
                          </SelectTrigger>
                          <SelectContent className="bg-white">
                            {salesPersons.map((person) => (
                              <SelectItem key={person.id} value={person.id.toString()}>
                                {person.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="delivery_date">納品日 *</Label>
                        <Input
                          id="delivery_date"
                          type="date"
                          value={newDeliveryNote.delivery_date}
                          onChange={(e) => {
                            const deliveryDate = e.target.value;
                            // 請求日を自動計算（20日締め）
                            let billingDate = '';
                            if (deliveryDate) {
                              const date = new Date(deliveryDate);
                              const day = date.getDate();
                              let billing: Date;
                              
                              if (day <= 20) {
                                // 1-20日 → 当月20日
                                billing = new Date(date.getFullYear(), date.getMonth(), 20);
                              } else {
                                // 21-31日 → 翌月20日
                                billing = new Date(date.getFullYear(), date.getMonth() + 1, 20);
                              }
                              
                              const year = billing.getFullYear();
                              const month = String(billing.getMonth() + 1).padStart(2, '0');
                              const day20 = String(billing.getDate()).padStart(2, '0');
                              billingDate = `${year}-${month}-${day20}`;
                            }
                            
                            setNewDeliveryNote({ 
                              ...newDeliveryNote, 
                              delivery_date: deliveryDate,
                              billing_date: billingDate
                            });
                          }}
                          className="w-48 bg-white"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="remarks">備考</Label>
                        <Input
                          id="remarks"
                          value={newDeliveryNote.remarks}
                          onChange={(e) => setNewDeliveryNote({ ...newDeliveryNote, remarks: e.target.value })}
                          className="w-full bg-white"
                          placeholder="任意"
                        />
                      </div>
                    </div>
                  </div>

                  {/* 商品明細 */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">商品明細</h3>
                    <div className="space-y-3">
                      {newDeliveryNote.details.map((detail, index) => {
                        const selectedProduct = products.find(p => p.id.toString() === detail.product_id);
                        return (
                          <div key={index} className="p-4 bg-gray-50 rounded-lg">
                            <div className="flex gap-3 items-end">
                              <div className="flex-1 space-y-2">
                                <Label>商品名 *</Label>
                                <Select value={detail.product_id} onValueChange={(value) => updateDetail(index, 'product_id', value)}>
                                  <SelectTrigger className="w-40 bg-white">
                                    <SelectValue placeholder="商品を選択" />
                                  </SelectTrigger>
                                  <SelectContent className="bg-white">
                                    {products.map((product) => (
                                      <SelectItem key={product.id} value={product.id.toString()}>
                                        {product.name} 
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
                                  value={detail.quantity}
                                  onChange={(e) => updateDetail(index, 'quantity', e.target.value)}
                                  className="w-15 bg-white"
                                  placeholder="0"
                                />
                              </div>
                              <Button
                                type="button"
                                size="sm"
                                onClick={() => removeDetail(index)}
                                className="bg-red-600 hover:bg-red-700 text-white"
                                disabled={newDeliveryNote.details.length === 1}
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
                          onClick={addDetail}
                          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium"
                        >
                          + 明細追加
                        </Button>
                      </div>

                    {/* 作成ボタン */}
                    <div className="flex justify-end gap-3 pt-4 border-t">
                      <Button 
                        variant="outline" 
                        onClick={() => {
                          setNewDeliveryNote({
                            sales_person_id: '',
                            tax_rate_id: '1',
                            delivery_date: '',
                            billing_date: '',
                            remarks: '',
                            details: [{ product_id: '', quantity: '' }]
                          });
                        }}
                      >
                        クリア
                      </Button>
                      <Button 
                        onClick={handleCreate} 
                        className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8"
                      >
                        作成
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

          {activeTab === 'recognition' && (
            <Card>
              <CardHeader>
                <CardTitle>納品書画像認識</CardTitle>
                <CardDescription>納品書の画像をアップロードして自動認識します</CardDescription>
              </CardHeader>
              <CardContent>
                {/* Image Upload Area */}
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    isDragActive
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <input {...getInputProps()} />
                  <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  {isDragActive ? (
                    <p className="text-lg text-blue-600">画像をここにドロップ...</p>
                  ) : (
                    <div>
                      <p className="text-lg text-gray-600 mb-2">
                        納品書の画像をドラッグ＆ドロップするか、クリックして選択してください
                      </p>
                      <p className="text-sm text-gray-500">
                        JPEG, PNG 形式に対応（複数ファイル可）
                      </p>
                    </div>
                  )}
                </div>

                {/* Recognition Status */}
                {isRecognizing && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-blue-800">画像を認識しています...</p>
                  </div>
                )}

                {/* Uploaded Images */}
                {uploadedImages.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-medium mb-4">認識結果</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {uploadedImages.map((image, index) => (
                        <Card key={index}>
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start mb-4">
                              <div className="flex items-center space-x-2">
                                <FileImage className="h-5 w-5 text-gray-500" />
                                <span className="text-sm text-gray-600 truncate max-w-[200px]">{image.file.name}</span>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeImage(index)}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                            
                            {/* 画像と認識結果を並べて表示 */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              {/* 画像エリア */}
                              <div className="space-y-2">
                                <img
                                  src={image.preview}
                                  alt="Uploaded"
                                  className="w-full h-auto object-contain rounded-lg border border-gray-200 cursor-pointer hover:opacity-90 transition-opacity"
                                  onClick={() => window.open(image.preview, '_blank')}
                                  title="クリックして拡大表示"
                                />
                                <p className="text-xs text-gray-500 text-center">クリックで拡大表示</p>
                              </div>
                              
                              {/* 認識結果エリア */}
                              <div>
                                {image.recognitionResult ? (
                                  <div className="space-y-2">
                                    {image.recognitionResult.success ? (
                                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg h-full flex flex-col">
                                        <p className="text-green-800 font-medium mb-3">✓ 認識成功</p>
                                        {/* 一時的なデバッグ情報 */}
                                        <div className="mb-2 p-2 bg-yellow-50 border border-yellow-300 rounded text-xs">
                                          <div>認識されたID: {JSON.stringify(image.recognitionResult?.salesPersonId)} (型: {typeof image.recognitionResult?.salesPersonId})</div>
                                          <div>販売員数: {salesPersons.length}</div>
                                          <div>販売員ID一覧: {salesPersons.slice(0, 5).map(sp => `${sp.id}(${sp.name})`).join(', ')}</div>
                                          <div>Number変換: {Number(image.recognitionResult?.salesPersonId)}</div>
                                          <div>検索結果: {JSON.stringify(salesPersons.find(sp => sp.id === Number(image.recognitionResult?.salesPersonId)))}</div>
                                        </div>
                                        <div className="space-y-2 text-sm text-green-700 flex-1">
                                          <div className="flex justify-between py-1 border-b border-green-200">
                                            <span className="font-medium">販売員:</span>
                                            <span>
                                              {salesPersons.find(sp => sp.id === Number(image.recognitionResult?.salesPersonId))?.name 
                                                || salesPersons.find(sp => String(sp.id) === String(image.recognitionResult?.salesPersonId))?.name
                                                || '不明'}
                                            </span>
                                          </div>
                                          <div className="flex justify-between py-1 border-b border-green-200">
                                            <span className="font-medium">納品日:</span>
                                            <span>{image.recognitionResult.deliveryDate}</span>
                                          </div>
                                          
                                          <div className="mt-3 pt-3 border-t border-green-300">
                                            <p className="font-medium mb-2">📋 商品明細:</p>
                                            <div className="space-y-1 max-h-[300px] overflow-y-auto">
                                              {image.recognitionResult.details?.map((detail, idx) => {
                                                const product = products.find(p => p.id === Number(detail.productId)) 
                                                  || products.find(p => String(p.id) === String(detail.productId));
                                                const amount = detail.quantity * detail.unitPrice;
                                                return (
                                                  <div key={idx} className="bg-white bg-opacity-70 p-2 rounded text-xs">
                                                    <div className="font-medium text-green-800">{product?.name || `商品ID:${detail.productId}`}</div>
                                                    <div className="flex justify-between mt-1 text-green-700">
                                                      <span>{detail.quantity}個 × ¥{detail.unitPrice.toLocaleString()}</span>
                                                      <span className="font-medium">¥{amount.toLocaleString()}</span>
                                                    </div>
                                                  </div>
                                                );
                                              })}
                                            </div>
                                            <div className="flex justify-between font-bold mt-3 pt-2 border-t border-green-400 text-base">
                                              <span>合計金額:</span>
                                              <span className="text-green-800">¥{image.recognitionResult.details?.reduce((sum, d) => sum + (d.quantity * d.unitPrice), 0).toLocaleString()}</span>
                                            </div>
                                          </div>
                                        </div>
                                        {image.isDuplicate && image.duplicateInfo && (
                                          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-300 rounded-lg">
                                            <div className="flex items-start">
                                              <span className="text-yellow-600 text-lg mr-2">⚠️</span>
                                              <div className="flex-1">
                                                <p className="text-sm font-semibold text-yellow-800">過去に認識した画像ですが登録しますか？</p>
                                                <p className="text-xs text-yellow-700 mt-1">
                                                  前回認識: {new Date(image.duplicateInfo.recognizedAt).toLocaleString()}
                                                  {' '}({image.duplicateInfo.success ? '成功' : '失敗'})
                                                </p>
                                              </div>
                                            </div>
                                          </div>
                                        )}
                                        <Button
                                          className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium"
                                          size="sm"
                                          onClick={() => {
                                            if (image.recognitionResult) {
                                              useRecognitionResult(image.recognitionResult);
                                            }
                                          }}
                                        >
                                          このデータを使用してDBに登録
                                        </Button>
                                      </div>
                                    ) : (
                                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg h-full">
                                        <p className="text-red-800 font-medium">✗ 認識失敗</p>
                                        <p className="text-sm text-red-700 mt-2">
                                          {image.recognitionResult.failureReason}
                                        </p>
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="flex items-center justify-center h-full min-h-[200px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                                    <p className="text-gray-500">認識処理中...</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
