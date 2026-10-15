import { Overview } from './overview';
import { fetchSystemInfo } from './system-info';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  return <Overview systemInfo={await fetchSystemInfo()} />;
}
