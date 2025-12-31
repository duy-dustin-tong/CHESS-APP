import React, { useState } from 'react';
import usePaginatedFetch from '../hooks/usePaginatedFetch';
import UserListItem from '../components/UserListItem';
import Button from '../components/Button';
import { useNavigate } from 'react-router-dom';

export default function UserSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [params, setParams] = useState({});

  const { items: users, loading, error, hasMore, loadMore, refresh } = usePaginatedFetch('/users/search', { pageSize: 10, params });

  const handleSubmit = (e) => {
    e && e.preventDefault();
    if (!query) return;
    // update params to trigger fetch
    setParams({ q: query });
  };

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input placeholder="Search username prefix" value={query} onChange={(e) => setQuery(e.target.value)} />
        <Button onClick={handleSubmit}>Search</Button>
        <Button onClick={() => { setQuery(''); setParams({}); refresh(); }}>Clear</Button>
        <Button onClick={() => navigate(-1)} style={{ marginLeft: 'auto' }}>Back</Button>
      </div>

      <div style={{ marginTop: 16 }}>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        {loading && users.length === 0 ? (
          <p>Searching...</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {users.map((u) => (
              <li key={u.id} style={{ marginBottom: 8 }}>
                <UserListItem user={u} showElo actions={[{ label: 'View', onClick: () => navigate(`/profile/${u.id}`) }]} />
              </li>
            ))}
          </ul>
        )}

        {hasMore && users.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Button onClick={loadMore}>{loading ? 'Loading...' : 'Load more'}</Button>
          </div>
        )}
      </div>
    </div>
  );
}
