const API_BASE_URL = 'https://bizpilot-backend.fly.dev/api';

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
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
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
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
    this.accessToken = data.access_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
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
    }
    return { data };
  }

  logout() {
    this.accessToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
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

  async updateDeliveryNote(id: number, deliveryNote: any) {
    return this.request(`/delivery-notes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(deliveryNote),
    });
  }

  async deleteDeliveryNote(id: number) {
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

  async updateInvoiceDiscountRate(invoiceId: number, discountRateId: number) {
    return this.request(`/sales-invoices/${invoiceId}/discount-rate`, {
      method: 'PATCH',
      body: JSON.stringify({ discount_rate_id: discountRateId }),
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

  async getSalesInvoice(invoiceId: number) {
    return this.request(`/sales-invoices/${invoiceId}`, {
      method: 'GET',
    });
  }

  async downloadInvoicePDF(invoiceId: number) {
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

  // Delete Sales Invoice
  async deleteSalesInvoice(invoiceId: number) {
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
}

export const apiClient = new ApiClient(API_BASE_URL);