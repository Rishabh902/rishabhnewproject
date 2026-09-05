import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
function errorMessage(error,fallback){const d=error.response?.data?.detail;if(typeof d==="string")return d;if(Array.isArray(d))return d.map(x=>x.msg).join(", ");return d?.message||fallback}
export default function Login(){
 const [mode,setMode]=useState("password"),[contact,setContact]=useState(""),[password,setPassword]=useState(""),[otp,setOtp]=useState(""),[devOtp,setDevOtp]=useState(""),[error,setError]=useState(""),[message,setMessage]=useState(""),[busy,setBusy]=useState(false);
 const {loginWithPassword,requestLoginOtp,loginWithOtp}=useAuth(); const navigate=useNavigate();
 const redirect=u=>navigate(u.role==="admin"?"/admin":"/dashboard",{replace:true});
 const submit=async e=>{e.preventDefault();setError("");setBusy(true);try{redirect(await loginWithPassword(contact,password))}catch(e){setError(errorMessage(e,"Login failed"))}finally{setBusy(false)}};
 const sendOtp=async()=>{setBusy(true);setError("");try{const d=await requestLoginOtp(contact);setDevOtp(d.dev_otp||"");setMessage(d.message)}catch(e){setError(errorMessage(e,"Unable to send OTP"))}finally{setBusy(false)}};
 const otpSubmit=async e=>{e.preventDefault();setBusy(true);setError("");try{redirect(await loginWithOtp(contact,otp))}catch(e){setError(errorMessage(e,"OTP login failed"))}finally{setBusy(false)}};
 return <main className="page"><section className="card"><h1>Login</h1><div className="tabs"><button type="button" className={mode==="password"?"tab active":"tab"} onClick={()=>setMode("password")}>Password</button><button type="button" className={mode==="otp"?"tab active":"tab"} onClick={()=>setMode("otp")}>OTP</button></div>
 <label>Mobile or email<input value={contact} onChange={e=>setContact(e.target.value)} required/></label>
 {mode==="password"?<form onSubmit={submit}><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required/></label><button disabled={busy}>{busy?"Signing in...":"Login"}</button><p><Link to="/forgot-password">Forgot password?</Link></p></form>:<><button type="button" onClick={sendOtp} disabled={busy||!contact}>{busy?"Sending...":"Send Login OTP"}</button>{devOtp&&<p className="dev-otp"><b>Development OTP:</b> {devOtp}</p>}{(devOtp||message)&&<form onSubmit={otpSubmit}><label>OTP<input value={otp} onChange={e=>setOtp(e.target.value)} maxLength={6} required/></label><button disabled={busy}>Login with OTP</button></form>}</>}
 {message&&<p className="message">{message}</p>}{error&&<p className="error">{error}</p>}<p>New user? <Link to="/register">Create account</Link></p>
 </section></main>
}
