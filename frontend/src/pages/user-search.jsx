import React, { useState } from 'react'
import usePaginatedFetch from '../hooks/usePaginatedFetch'
import UserListItem from '../components/UserListItem'
import ListShell from '../components/ListShell'
import Button from '../components/Button'
import { useNavigate } from 'react-router-dom'

export default function UserSearch(){
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const { items: users, loading, error, hasMore, loadMore, refresh } = usePaginatedFetch('/users/users/search', { pageSize: 20, params: { q } })

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Search Users</h1>
        <Button onClick={() => navigate('/')}>Home</Button>
      </div>
      <div style={{ marginBottom: 12 }}>
        <input value={q} onChange={(e)=>setQ(e.target.value)} placeholder="username prefix" />
        <Button onClick={refresh} style={{ marginLeft: 8 }}>Search</Button>
      </div>

      <ListShell loading={loading} emptyMessage="No users found">
        {error && <div style={{ color: 'red' }}>{String(error)}</div>}
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {users.map(u => (
            <UserListItem key={u.id} user={u} showElo />
          ))}
        </ul>
        {hasMore && <Button onClick={loadMore}>Load more</Button>}
      </ListShell>
    </div>
  )
}
