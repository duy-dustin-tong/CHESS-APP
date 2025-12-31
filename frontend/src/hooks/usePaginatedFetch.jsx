import { useState, useEffect, useCallback } from 'react';
import api from '../api/api';

export default function usePaginatedFetch(endpoint, { pageSize = 20, params = {} } = {}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  // stringify params to produce a stable dependency key
  const paramsKey = JSON.stringify(params || {});

  const loadPage = useCallback(async (newOffset = 0, replace = false) => {
    setLoading(true);
    setError(null);
    try {
      // use the current params value from closure; loadPage is recreated when paramsKey changes
      const res = await api.get(endpoint, { params: { ...(params || {}), limit: pageSize, offset: newOffset } });
      const data = res.data || [];
      setItems((prev) => (replace ? data : [...prev, ...data]));
      setHasMore(data.length === pageSize);
      setOffset(newOffset + data.length);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [endpoint, pageSize, paramsKey]);

  useEffect(() => {
    // reset when endpoint or params change
    setItems([]);
    setOffset(0);
    setHasMore(true);
    loadPage(0, true);
  }, [endpoint, paramsKey, loadPage]);

  const loadMore = useCallback(() => {
    if (loading || !hasMore) return;
    loadPage(offset, false);
  }, [loading, hasMore, loadPage, offset]);

  const refresh = useCallback(() => {
    setItems([]);
    setOffset(0);
    setHasMore(true);
    loadPage(0, true);
  }, [loadPage]);

  return { items, loading, error, hasMore, loadMore, refresh };
}
