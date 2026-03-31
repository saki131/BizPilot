'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

const PRESET_MODELS = [
  'gemini-2.0-flash',
  'gemini-2.5-flash',
  'gemini-2.5-flash-lite-preview-06-17',
  'gemini-3.1-flash-lite-preview',
];

export default function SettingsPage() {
  const router = useRouter();
  const [model, setModel] = useState('');
  const [fallbackModel, setFallbackModel] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const username = typeof window !== 'undefined' ? localStorage.getItem('username') : null;
    if (username !== 'admin') {
      router.push('/delivery-notes');
      return;
    }
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    const result = await apiClient.getGeminiModelSetting();
    if (result.data) {
      setModel(result.data.model);
      setFallbackModel(result.data.fallback_model);
    } else {
      setErrorMessage(result.error || '設定の取得に失敗しました');
    }
    setLoading(false);
  };

  const handleSave = async () => {
    if (!model.trim() || !fallbackModel.trim()) {
      setErrorMessage('モデル名を入力してください');
      return;
    }
    setSaving(true);
    setErrorMessage('');
    setSuccessMessage('');
    const result = await apiClient.updateGeminiModelSetting({
      model: model.trim(),
      fallback_model: fallbackModel.trim(),
    });
    if (result.data) {
      setModel(result.data.model);
      setFallbackModel(result.data.fallback_model);
      setSuccessMessage('設定を保存しました');
      setTimeout(() => setSuccessMessage(''), 3000);
    } else {
      setErrorMessage(result.error || '設定の保存に失敗しました');
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">読み込み中...</p>
      </div>
    );
  }

  return (
    <main className="pb-24 px-4 pt-4 max-w-lg mx-auto">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Gemini API バージョン設定</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {successMessage && (
            <Alert className="border-green-400 bg-green-50">
              <AlertDescription className="text-green-700">{successMessage}</AlertDescription>
            </Alert>
          )}
          {errorMessage && (
            <Alert variant="destructive">
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="model">プライマリモデル</Label>
            <Input
              id="model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="例: gemini-2.5-flash"
            />
            <div className="flex flex-wrap gap-2 mt-2">
              {PRESET_MODELS.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setModel(m)}
                  className={`text-xs px-2 py-1 rounded border transition-colors ${
                    model === m
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="fallbackModel">フォールバックモデル</Label>
            <Input
              id="fallbackModel"
              value={fallbackModel}
              onChange={(e) => setFallbackModel(e.target.value)}
              placeholder="例: gemini-2.5-flash"
            />
            <div className="flex flex-wrap gap-2 mt-2">
              {PRESET_MODELS.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setFallbackModel(m)}
                  className={`text-xs px-2 py-1 rounded border transition-colors ${
                    fallbackModel === m
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <p className="text-xs text-gray-500">
            ※ プライマリモデルが失敗した場合、フォールバックモデルが使用されます。
          </p>

          <Button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {saving ? '保存中...' : '保存'}
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
