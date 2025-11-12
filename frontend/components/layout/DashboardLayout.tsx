'use client';

import { ReactNode } from 'react';
import Sidebar from './Sidebar';

export default function DashboardLayout({ children }: { children: ReactNode }) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
            <Sidebar />
            <main className="ml-64 p-8">
                {children}
            </main>
        </div>
    );
}
