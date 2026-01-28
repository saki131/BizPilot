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

export default function MastersPage() {
  const [salesPersons, setSalesPersons] = useState<SalesPerson[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [contractors, setContractors] = useState<Contractor[]>([]);
  const [activeTab, setActiveTab] = useState<'sales-persons' | 'products' | 'contractors'>('sales-persons');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newItem, setNewItem] = useState({ name: '', price: '' });
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [salesPersonsRes, productsRes, contractorsRes] = await Promise.all([
        apiClient.getSalesPersons(),
        apiClient.getProducts(),
        apiClient.getContractors(),
      ]);

      if (salesPersonsRes.data) setSalesPersons(salesPersonsRes.data as SalesPerson[]);
      if (productsRes.data) setProducts(productsRes.data as Product[]);
      if (contractorsRes.data) setContractors(contractorsRes.data as Contractor[]);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleCreate = async () => {
    try {
      let result;
      if (activeTab === 'sales-persons') {
        result = await apiClient.createSalesPerson({ name: newItem.name });
      } else if (activeTab === 'products') {
        result = await apiClient.createProduct({ name: newItem.name, price: parseInt(newItem.price) });
      } else if (activeTab === 'contractors') {
        result = await apiClient.createContractor({ name: newItem.name });
      }

      if (result?.data) {
        setIsDialogOpen(false);
        setNewItem({ name: '', price: '' });
        loadData();
      }
    } catch (error) {
      console.error('Failed to create item:', error);
    }
  };

  const renderTable = () => {
    if (activeTab === 'sales-persons') {
      return (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>名前</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {salesPersons.map((person) => (
              <TableRow key={person.id}>
                <TableCell>{person.id}</TableCell>
                <TableCell>{person.name}</TableCell>
                <TableCell>
                  <Button variant="outline" size="sm">編集</Button>
                  <Button variant="destructive" size="sm" className="ml-2">削除</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );
    } else if (activeTab === 'products') {
      return (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>商品名</TableHead>
              <TableHead>価格</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {products.map((product) => (
              <TableRow key={product.id}>
                <TableCell>{product.id}</TableCell>
                <TableCell>{product.name}</TableCell>
                <TableCell>{product.price}</TableCell>
                <TableCell>
                  <Button variant="outline" size="sm">編集</Button>
                  <Button variant="destructive" size="sm" className="ml-2">削除</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );
    } else if (activeTab === 'contractors') {
      return (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>契約者名</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {contractors.map((contractor) => (
              <TableRow key={contractor.id}>
                <TableCell>{contractor.id}</TableCell>
                <TableCell>{contractor.name}</TableCell>
                <TableCell>
                  <Button variant="outline" size="sm">編集</Button>
                  <Button variant="destructive" size="sm" className="ml-2">削除</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">マスタ管理</h1>
            <Button onClick={() => router.push('/dashboard')} variant="outline">
              ダッシュボードに戻る
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-6">
            <div className="flex space-x-4">
              <Button
                variant={activeTab === 'sales-persons' ? 'default' : 'outline'}
                onClick={() => setActiveTab('sales-persons')}
              >
                営業担当
              </Button>
              <Button
                variant={activeTab === 'products' ? 'default' : 'outline'}
                onClick={() => setActiveTab('products')}
              >
                商品
              </Button>
              <Button
                variant={activeTab === 'contractors' ? 'default' : 'outline'}
                onClick={() => setActiveTab('contractors')}
              >
                契約者
              </Button>
            </div>
          </div>

          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>
                    {activeTab === 'sales-persons' && '営業担当一覧'}
                    {activeTab === 'products' && '商品一覧'}
                    {activeTab === 'contractors' && '契約者一覧'}
                  </CardTitle>
                  <CardDescription>
                    {activeTab === 'sales-persons' && '営業担当の管理を行います'}
                    {activeTab === 'products' && '商品の管理を行います'}
                    {activeTab === 'contractors' && '契約者の管理を行います'}
                  </CardDescription>
                </div>
                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                  <DialogTrigger asChild>
                    <Button>新規作成</Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>
                        {activeTab === 'sales-persons' && '営業担当新規作成'}
                        {activeTab === 'products' && '商品新規作成'}
                        {activeTab === 'contractors' && '契約者新規作成'}
                      </DialogTitle>
                      <DialogDescription>
                        新しい項目を作成します。
                      </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                      <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="name" className="text-right">
                          名前
                        </Label>
                        <Input
                          id="name"
                          value={newItem.name}
                          onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                          className="col-span-3"
                        />
                      </div>
                      {activeTab === 'products' && (
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label htmlFor="price" className="text-right">
                            価格
                          </Label>
                          <Input
                            id="price"
                            type="number"
                            value={newItem.price}
                            onChange={(e) => setNewItem({ ...newItem, price: e.target.value })}
                            className="col-span-3"
                          />
                        </div>
                      )}
                    </div>
                    <div className="flex justify-end">
                      <Button onClick={handleCreate}>作成</Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {renderTable()}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}