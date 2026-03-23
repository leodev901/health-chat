import { Suspense } from 'react';

async function fetchHealthSettings() {
  const res = await fetch(`${process.env.API_BASE_URL}/healthz`, {
    cache: 'no-store',
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch healthz data');
  }

  return res.text();
}

export default async function Home() {
  const healthzResult = await fetchHealthSettings();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-2xl font-bold mb-4">Health Check Result</h1>
      <pre className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm">
        {healthzResult}
      </pre>
    </main>
  );
}
