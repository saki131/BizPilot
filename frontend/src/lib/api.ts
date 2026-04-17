const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://bizpilot-backend.fly.dev/api';

// Debug: Log the API URL being used (only in browser)
if (typeof window !== 'undefined') {
  console.log('API Base URL:', API_BASE_URL);
  console.log('Environment:', process.env.NODE_ENV);
}

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  username: string;
}

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

class ApiClient {
  private baseURL: string;
  private accessToken: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    // Token will be loaded dynamically in getAccessToken()
  }

  private getAccessToken(): string | null {
    // Always try to get the latest token from localStorage
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        this.accessToken = storedToken;
      }
    }
    return this.accessToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    // Debug: Log the full URL being requested
    console.log('Making request to:', url, 'Method:', options.method || 'GET');

    // If body is FormData, let the browser set the Content-Type (with boundary).
    const isFormData = (typeof FormData !== 'undefined') && options.body instanceof FormData;
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (!isFormData) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }

    const token = this.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401 && token) {
        // Try to refresh token
        const refreshResult = await this.refreshToken();
        if (refreshResult.data) {
          // Retry the original request with new token
          headers['Authorization'] = `Bearer ${this.accessToken}`;
          const retryResponse = await fetch(url, {
            ...options,
            headers,
          });
          if (retryResponse.ok) {
            const data = await retryResponse.json();
            return { data };
          }
        } else {
          // Refresh failed, clear tokens and redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
          return { error: 'Session expired. Please login again.' };
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        console.error('API Error:', {
          status: response.status,
          statusText: response.statusText,
          errorData: errorData
        });
        
        // Handle validation errors (422)
        if (response.status === 422 && errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // FastAPI validation errors format
            const errors = errorData.detail.map((err: any) => 
              `${err.loc.join('.')}: ${err.msg}`
            ).join(', ');
            return { error: `Validation error: ${errors}` };
          }
        }
        
        return { error: errorData.detail || errorData.message || 'Request failed' };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Network error' };
    }
  }

  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: credentials.username,
        password: credentials.password,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Login failed' }));
      return { error: errorData.detail || errorData.message };
    }

    const data = await response.json();
    console.log('[API] Login response:', data);
    this.accessToken = data.access_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      if (data.username) {
        localStorage.setItem('username', data.username);
        console.log('[API] Saved username to localStorage:', data.username);
      } else {
        console.warn('[API] No username in login response!');
      }
      // middleware認証用Cookieからもトークンを参照できるように設定
      document.cookie = `access_token=${data.access_token}; path=/; SameSite=Strict; max-age=3600`;
    }
    return { data };
  }

  async refreshToken(): Promise<ApiResponse<LoginResponse>> {
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
    if (!refreshToken) {
      return { error: 'No refresh token available' };
    }

    const response = await fetch(`${this.baseURL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Token refresh failed' }));
      return { error: errorData.detail || errorData.message };
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      if (data.username) {
        localStorage.setItem('username', data.username);
      }
      // Cookieも更新
      document.cookie = `access_token=${data.access_token}; path=/; SameSite=Strict; max-age=3600`;
    }
    return { data };
  }

  logout() {
    this.accessToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('username');
      // Cookieも削除
      document.cookie = 'access_token=; path=/; SameSite=Strict; max-age=0';
    }
  }

  // Masters API
  async getSalesPersons() {
    return this.request('/masters/sales-persons');
  }

  async createSalesPerson(data: any) {
    return this.request('/masters/sales-persons', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateSalesPerson(id: number, data: any) {
    return this.request(`/masters/sales-persons/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteSalesPerson(id: number) {
    return this.request(`/masters/sales-persons/${id}`, {
      method: 'DELETE',
    });
  }

  async getProducts() {
    return this.request('/masters/products');
  }

  async createProduct(data: any) {
    return this.request('/masters/products', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProduct(id: number, data: any) {
    return this.request(`/masters/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProduct(id: number) {
    return this.request(`/masters/products/${id}`, {
      method: 'DELETE',
    });
  }

  async getContractors() {
    return this.request('/masters/contractors');
  }

  async createContractor(data: any) {
    return this.request('/masters/contractors', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateContractor(id: number, data: any) {
    return this.request(`/masters/contractors/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteContractor(id: number) {
    return this.request(`/masters/contractors/${id}`, {
      method: 'DELETE',
    });
  }

  // Delivery Notes API
  async getDeliveryNotes() {
    return this.request('/delivery-notes/');
  }

  async createDeliveryNote(deliveryNote: any) {
    return this.request('/delivery-notes/', {
      method: 'POST',
      body: JSON.stringify(deliveryNote),
    });
  }

  async updateDeliveryNote(id: string, deliveryNote: any) {
    return this.request(`/delivery-notes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(deliveryNote),
    });
  }

  async deleteDeliveryNote(id: string) {
    return this.request(`/delivery-notes/${id}`, {
      method: 'DELETE',
    });
  }

  async recognizeImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/delivery-notes/recognize-image', {
      method: 'POST',
      body: formData,
    });
  }

  // Sales Invoices API
  async bulkGenerateSalesInvoices(data: {
    closing_date: string;
    sales_person_ids?: number[];
  }) {
    return this.request('/sales-invoices/bulk-generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateInvoiceDiscountRate(invoiceId: string, discountRateId: number) {
    return this.request(`/sales-invoices/${invoiceId}/discount-rate`, {
      method: 'PATCH',
      body: JSON.stringify({ discount_rate_id: discountRateId }),
    });
  }

  async updateInvoice(invoiceId: string, data: { discount_rate_id?: number; note?: string }) {
    return this.request(`/sales-invoices/${invoiceId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async generateSalesInvoice(data: {
    sales_person_id: number;
    start_date: string;
    end_date: string;
    discount_rate_id: number;
  }) {
    return this.request('/sales-invoices/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSalesInvoices(salesPersonId?: number) {
    const params = salesPersonId ? `?sales_person_id=${salesPersonId}` : '';
    return this.request(`/sales-invoices${params}`, {
      method: 'GET',
    });
  }

  async getSalesInvoice(invoiceId: string) {
    return this.request(`/sales-invoices/${invoiceId}`, {
      method: 'GET',
    });
  }

  async downloadInvoicePDF(invoiceId: string) {
    const url = `${this.baseURL}/sales-invoices/${invoiceId}/pdf`;
    const headers: Record<string, string> = {};
    
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to download PDF');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `invoice_${invoiceId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  }

  async downloadContractorInvoicePDF(invoiceId: string) {
    const url = `${this.baseURL}/contractor-invoices/${invoiceId}/pdf`;
    const headers: Record<string, string> = {};
    
    const token = this.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to download PDF');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `contractor_invoice_${invoiceId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  }

  async downloadSalesReceiptPDF(invoiceId: string) {
    const url = `${this.baseURL}/sales-invoices/${invoiceId}/receipt-pdf`;
    const headers: Record<string, string> = {};
    
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to download receipt PDF');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `sales_receipt_${invoiceId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  }

  async downloadContractorReceiptPDF(invoiceId: string) {
    const url = `${this.baseURL}/contractor-invoices/${invoiceId}/receipt-pdf`;
    const headers: Record<string, string> = {};
    
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to download receipt PDF');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `contractor_receipt_${invoiceId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Delete Sales Invoice
  async deleteSalesInvoice(invoiceId: string) {
    return this.request(`/sales-invoices/${invoiceId}`, {
      method: 'DELETE',
    });
  }

  // Discount Rates API
  async getDiscountRates() {
    return this.request('/masters/discount-rates', {
      method: 'GET',
    });
  }

  // Tax Rates API
  async getTaxRates() {
    return this.request('/masters/tax-rates', {
      method: 'GET',
    });
  }

  // Contractor Invoices API
  async createContractorInvoice(data: {
    contractor_id: number;
    tax_rate_id: number;
    invoice_date: string;
    note?: string;
    details: Array<{ product_id: number; total_quantity: number; unit_price?: number }>;
  }) {
    return this.request('/contractor-invoices/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getContractorInvoices() {
    return this.request('/contractor-invoices/', {
      method: 'GET',
    });
  }

  async getContractorInvoice(invoiceId: string) {
    return this.request(`/contractor-invoices/${invoiceId}`, {
      method: 'GET',
    });
  }

  async updateContractorInvoice(invoiceId: string, data: {
    discount_rate_id?: number;
    invoice_date?: string;
    receipt_date?: string;
    note?: string;
    details?: Array<{ product_id: number; total_quantity: number; unit_price?: number }>;
  }) {
    return this.request(`/contractor-invoices/${invoiceId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteContractorInvoice(invoiceId: string) {
    return this.request(`/contractor-invoices/${invoiceId}`, {
      method: 'DELETE',
    });
  }

  // Sales Stats API
  async getSalesMonthlyTotals(year?: number) {
    const params = year ? `?year=${year}` : '';
    return this.request<Array<{
      year_month: string;
      sales_invoice_total: number;
      contractor_invoice_total: number;
      grand_total: number;
    }>>(`/sales-stats/monthly-totals${params}`, { method: 'GET' });
  }

  async getSalesMonthlyProductQuantities(year: number, month: number) {
    return this.request<Array<{
      product_id: number;
      product_name: string;
      display_order: number;
      sales_total_quantity: number;
      contractor_total_quantity: number;
      grand_total_quantity: number;
    }>>(`/sales-stats/monthly-product-quantities?year=${year}&month=${month}`, { method: 'GET' });
  }

  // Customers API (マスタ)
  async getCustomers() {
    return this.request('/masters/customers');
  }

  async createCustomer(data: { name: string; name_kana?: string }) {
    return this.request('/masters/customers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCustomer(id: number, data: { name: string; name_kana?: string }) {
    return this.request(`/masters/customers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCustomer(id: number) {
    return this.request(`/masters/customers/${id}`, {
      method: 'DELETE',
    });
  }

  // Customer Orders API
  async getCustomerOrders(params?: { status?: string; customer_id?: number; due_from?: string; due_to?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.customer_id) searchParams.append('customer_id', params.customer_id.toString());
    if (params?.due_from) searchParams.append('due_from', params.due_from);
    if (params?.due_to) searchParams.append('due_to', params.due_to);
    const qs = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request(`/customer-orders/${qs}`, { method: 'GET' });
  }

  async createCustomerOrder(data: { customer_id: number; order_amount: number; order_date?: string; memo?: string }) {
    return this.request('/customer-orders/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async createCustomerOrdersBulk(data: { orders: Array<{ customer_name: string; name_kana?: string; order_amount: number; order_date?: string; memo?: string }> }) {
    return this.request('/customer-orders/bulk', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async recognizeOrderImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/customer-orders/recognize-image', {
      method: 'POST',
      body: formData,
    });
  }

  async updateCustomerOrder(orderId: string, data: { customer_id?: number; order_date?: string; order_amount?: number; payment_due_date?: string; memo?: string }) {
    return this.request(`/customer-orders/${orderId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCustomerOrder(orderId: string) {
    return this.request(`/customer-orders/${orderId}`, {
      method: 'DELETE',
    });
  }

  // Deposit Records API
  async uploadDepositsCSV(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/customer-orders/deposits/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async confirmMatch(depositId: string, orderId: string) {
    return this.request('/customer-orders/deposits/confirm-match', {
      method: 'POST',
      body: JSON.stringify({ deposit_id: depositId, order_id: orderId }),
    });
  }

  async getDepositRecords() {
    return this.request('/customer-orders/deposits/', { method: 'GET' });
  }

  async checkPayments() {
    return this.request('/customer-orders/deposits/check-payments', {
      method: 'POST',
    });
  }

  async updateOrderPaymentStatus(orderId: string, data: { payment_status: string; deposit_record_id?: string | null }) {
    return this.request(`/customer-orders/${orderId}/payment-status`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Admin Settings API
  async getGeminiModelSetting() {
    return this.request<{ model: string; fallback_model: string }>('/admin/settings/gemini-model');
  }

  async updateGeminiModelSetting(data: { model: string; fallback_model: string }) {
    return this.request<{ model: string; fallback_model: string }>('/admin/settings/gemini-model', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);