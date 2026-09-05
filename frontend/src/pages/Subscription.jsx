import React, { useEffect, useState } from "react";
import api from "../api/client";

const RAZORPAY_SCRIPT = "https://checkout.razorpay.com/v1/checkout.js";

function loadRazorpay() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) return resolve(true);
    const script = document.createElement("script");
    script.src = RAZORPAY_SCRIPT;
    script.onload = () => resolve(true);
    script.onerror = () => reject(new Error("Could not load payment checkout."));
    document.body.appendChild(script);
  });
}

export default function Subscription() {
  const [plans, setPlans] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [coupon, setCoupon] = useState("");
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.get("/api/subscriptions/plans"), api.get("/api/subscriptions/me")])
      .then(([p, s]) => { setPlans(p.data || []); setSubscription(s.data); })
      .catch((err) => setError(err.response?.data?.detail || "Could not load subscriptions."))
      .finally(() => setLoading(false));
  }, []);

  const selectPlan = (plan) => {
    setSelectedPlan(plan);
    setCoupon("");
    setQuote(null);
    setError(null);
  };

  const previewCoupon = async () => {
    if (!selectedPlan || !coupon.trim()) return;
    try {
      setError(null);
      const { data } = await api.post("/api/payments/coupon-preview", { plan_code: selectedPlan.code, coupon_code: coupon.trim() });
      setQuote(data);
    } catch (err) {
      setQuote(null);
      setError(err.response?.data?.detail || "Coupon could not be applied.");
    }
  };

  const pay = async () => {
    if (!selectedPlan) return;
    setPaying(true);
    setError(null);
    try {
      await loadRazorpay();
      const { data: order } = await api.post("/api/payments/orders", {
        plan_code: selectedPlan.code,
        coupon_code: coupon.trim() || null,
      });

      const keyResponse = await api.get("/api/payments/checkout-config");
      const options = {
        key: keyResponse.data.key_id,
        amount: Math.round(order.final_amount_inr * 100),
        currency: order.currency,
        name: "MauryaShaadi",
        description: `${selectedPlan.name} - ${selectedPlan.duration_days} days`,
        order_id: order.gateway_order_id,
        prefill: {},
        theme: { color: "#2563eb" },
        handler: async (response) => {
          try {
            await api.post("/api/payments/verify", response);
            const { data } = await api.get("/api/subscriptions/me");
            setSubscription(data);
            setSelectedPlan(null);
            alert("Payment successful. Your AI matching subscription is now active.");
          } catch (err) {
            setError(err.response?.data?.detail || "Payment completed but server verification failed. Please contact support with your payment ID.");
          } finally {
            setPaying(false);
          }
        },
        modal: { ondismiss: () => setPaying(false) },
      };
      const checkout = new window.Razorpay(options);
      checkout.on("payment.failed", (response) => {
        setError(response.error?.description || "Payment failed.");
        setPaying(false);
      });
      checkout.open();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Could not start payment.");
      setPaying(false);
    }
  };

  if (loading) return <div className="p-10 text-center">Loading subscription plans...</div>;

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-black text-gray-900">AI Matching Plans</h1>
        <p className="text-gray-600 mt-2">Choose how much AI compatibility access you want.</p>
      </div>

      {subscription && <div className="mb-6 p-4 rounded-2xl bg-green-50 border border-green-200 text-green-800">
        <strong>Active: {subscription.plan_code}</strong> · Up to {subscription.max_match_score}% AI compatibility · Expires {new Date(subscription.end_date).toLocaleDateString("en-IN")}
      </div>}

      {error && <div className="mb-6 p-4 rounded-xl bg-red-50 text-red-700">{error}</div>}

      <div className="grid md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div key={plan.id} className={`border rounded-2xl p-6 bg-white shadow-sm ${selectedPlan?.id === plan.id ? "ring-2 ring-blue-500" : ""}`}>
            <h2 className="text-xl font-bold">{plan.name}</h2>
            <div className="my-4"><span className="text-4xl font-black">₹{plan.price_inr}</span><span className="text-gray-500"> / month</span></div>
            <div className="mb-5 text-sm font-semibold text-blue-700">Up to {plan.max_match_score}% AI compatibility</div>
            <ul className="space-y-2 text-sm text-gray-600 min-h-32">{plan.features.map((f) => <li key={f}>✓ {f}</li>)}</ul>
            <button onClick={() => selectPlan(plan)} className="w-full mt-5 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl">Choose plan</button>
          </div>
        ))}
      </div>

      {selectedPlan && <div className="max-w-xl mx-auto mt-8 p-6 bg-white border rounded-2xl shadow-sm">
        <h3 className="text-xl font-bold">Checkout · {selectedPlan.name}</h3>
        <div className="flex gap-2 mt-4">
          <input value={coupon} onChange={(e) => setCoupon(e.target.value.toUpperCase())} placeholder="Coupon code (optional)" className="flex-1 border rounded-xl px-4 py-3" />
          <button onClick={previewCoupon} disabled={!coupon.trim()} className="px-4 py-3 rounded-xl bg-gray-100 font-semibold disabled:opacity-50">Apply</button>
        </div>
        <div className="mt-4 p-4 rounded-xl bg-gray-50 text-sm">
          <div className="flex justify-between"><span>Plan</span><strong>₹{selectedPlan.price_inr.toFixed(2)}</strong></div>
          {quote && <div className="flex justify-between text-green-700 mt-2"><span>Discount</span><strong>- ₹{quote.discount_amount_inr.toFixed(2)}</strong></div>}
          <div className="flex justify-between text-lg font-black mt-3 pt-3 border-t"><span>Total</span><span>₹{quote ? quote.final_amount_inr.toFixed(2) : selectedPlan.price_inr.toFixed(2)}</span></div>
        </div>
        <button onClick={pay} disabled={paying} className="w-full mt-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold disabled:opacity-50">{paying ? "Opening secure checkout..." : "Pay securely"}</button>
        <button onClick={() => setSelectedPlan(null)} className="w-full mt-2 py-2 text-sm text-gray-500">Cancel</button>
      </div>}
    </div>
  );
}
