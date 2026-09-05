import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
export default function ForgotPassword(){
 const [email,setEmail]=useState(""),[message,setMessage]=useState(""),[error,setError]=useState(""),[busy,setBusy]=useState(false),[dev,setDev]=useState("");
 const submit=async e=>{e.preventDefault();setBusy(true);setError("");try{const {data}=await api.post("/api/auth/forgot-password",{email});setMessage(data.message);setDev(data.dev_reset_url||"")}catch(e){setError(e.response?.data?.detail||"Unable to send reset email")}finally{setBusy(false)}};
 return <main className="page"><section className="card"><h1>Forgot password</h1><p>Enter your registered email. We will send a secure password reset link.</p><form onSubmit={submit}><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label><button disabled={busy}>{busy?"Sending...":"Send reset link"}</button></form>{message&&<p className="message">{message}</p>}{dev&&<p className="dev-otp">Development reset link: <a href={dev}>Open reset link</a></p>}{error&&<p className="error">{error}</p>}<p><Link to="/login">Back to login</Link></p></section></main>
}
