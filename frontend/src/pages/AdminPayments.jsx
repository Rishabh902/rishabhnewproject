import React, { useEffect, useState } from "react";
import api from "../api/client";

export default function AdminPaymentsDashboard() {
  const [orders, setOrders] = useState([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState(null);

  const load = async () => {
    try {
      setError(null);
      const response = await api.get("/api/admin/payments", { params: status ? { status_filter: status } : {} });
      setOrders(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load payment records.");
    }
  };

  useEffect(() => { load(); }, [status]);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-black text-gray-900">Payment Transactions</h1>
          <p className="text-sm text-gray-500 mt-1">Gateway-backed orders. Subscription activation happens only after server-side payment verification.</p>
        </div>
        <div className="flex gap-2">
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="border rounded-xl px-3 py-2 text-sm">
            <option value="">All statuses</option>
            <option value="CREATED">Created</option>
            <option value="PAID">Paid</option>
            <option value="FAILED">Failed</option>
          </select>
          <button onClick={load} className="bg-gray-100 px-4 py-2 rounded-xl text-sm font-semibold">Refresh</button>
        </div>
      </div>
      {error && <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-xl">{error}</div>}
      <div className="overflow-x-auto bg-white border rounded-2xl shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500">
            <tr><th className="p-4">Order</th><th className="p-4">User</th><th className="p-4">Plan</th><th className="p-4">Amount</th><th className="p-4">Discount</th><th className="p-4">Gateway</th><th className="p-4">Status</th><th className="p-4">Created</th></tr>
          </thead>
          <tbody className="divide-y">
            {orders.map((o) => <tr key={o.id}>
              <td className="p-4 font-mono">{o.order_reference}</td>
              <td className="p-4">#{o.user_id}</td>
              <td className="p-4 font-semibold">{o.plan_code}</td>
              <td className="p-4">₹{o.final_amount_inr?.toFixed(2)}</td>
              <td className="p-4">₹{o.discount_amount_inr?.toFixed(2)}</td>
              <td className="p-4">{o.gateway}</td>
              <td className="p-4 font-bold">{o.status}</td>
              <td className="p-4 text-gray-500">{new Date(o.created_at).toLocaleString("en-IN")}</td>
            </tr>)}
          </tbody>
        </table>
        {!orders.length && <div className="p-12 text-center text-gray-500">No payment orders found.</div>}
      </div>
    </div>
  );
}
