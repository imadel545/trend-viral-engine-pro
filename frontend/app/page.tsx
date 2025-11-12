/**
 * Home Page - Redirects to Dashboard
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.push('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-12 w-12 text-purple-400 animate-spin mx-auto mb-4" />
        <p className="text-white text-lg">Chargement du dashboard...</p>
      </div>
    </div>
  );
}
