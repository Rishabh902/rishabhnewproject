import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import api from "../api/client";
export default function ResetPassword(){
 const [params]=useSearchParams(); const token=params.get("token")||""; const [password,setPassword]=useState(""),[confirm,setConfirm]=useState(""),[message,setMessage]=useState(""),[error,setError]=useState(""),[busy,setBusy]=useState(false); const navigate=useNavigate();
 const submit=async e=>{e.preventDefault();setError("");if(password!==confirm){setError("Password and confirm password do not match.");return}setBusy(true);try{const {data}=await api.post("/api/auth/reset-password",{token,password,confirm_password:confirm});setMessage(data.message);setTimeout(()=>navigate("/login"),1200)}catch(e){setError(e.response?.data?.detail||"Reset link is invalid or expired")}finally{setBusy(false)}};
 return <main className="page"><section className="card"><h1>Create new password</h1>{!token?<p className="error">Invalid reset link.</p>:<form onSubmit={submit}><label>New password<input type="password" minLength={8} value={password} onChange={e=>setPassword(e.target.value)} required/></label><label>Confirm password<input type="password" minLength={8} value={confirm} onChange={e=>setConfirm(e.target.value)} required/></label><button disabled={busy}>{busy?"Saving...":"Create new password"}</button></form>}{message&&<p className="message">{message}</p>}{error&&<p className="error">{error}</p>}<p><Link to="/login">Back to login</Link></p></section></main>
}
