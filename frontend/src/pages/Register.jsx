import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/client";
import { STATES, DISTRICTS, CASTES } from "../data/options";

function errorText(e, fallback) {
  const d=e.response?.data?.detail;
  if (typeof d==="string") return d;
  if (Array.isArray(d)) return d.map(x=>x.msg).join(", ");
  return d?.message || fallback;
}
function minAdultDob(){const d=new Date();d.setFullYear(d.getFullYear()-18);return d.toISOString().slice(0,10)}

export default function Register(){
 const [step,setStep]=useState(1);
 const [account,setAccount]=useState({phone:"",email:"",password:"",confirm_password:"",profile_for:"self",relationship:"",registration_location:""});
 const [profile,setProfile]=useState({name:"",gender:"",date_of_birth:"",caste:"",state:"",district:"",city_or_village:"",permanent_address:"",preferred_location:""});
 const [otp,setOtp]=useState(""); const [registration,setRegistration]=useState(null); const [message,setMessage]=useState(""); const [busy,setBusy]=useState(false); const navigate=useNavigate();
 const ch=(setter)=>(e)=>setter(v=>({...v,[e.target.name]:e.target.value}));
 const register=async(e)=>{e.preventDefault();setMessage("");if(account.password!==account.confirm_password){setMessage("Password and confirm password do not match.");return}setBusy(true);try{const {data}=await api.post("/api/auth/register",account);setRegistration(data);setStep(2);setMessage(data.message)}catch(e){setMessage(errorText(e,"Registration failed"))}finally{setBusy(false)}};
 const saveBasic=async(e)=>{e.preventDefault();setBusy(true);setMessage("");try{const {data}=await api.post("/api/auth/register/profile",{...profile,registration_token:registration.registration_token});setMessage(data.message);setStep(3)}catch(e){setMessage(errorText(e,"Unable to save profile"))}finally{setBusy(false)}};
 const verify=async(e)=>{e.preventDefault();setBusy(true);try{await api.post("/api/auth/otp/verify",{contact:registration.otp_contact,otp,registration_token:registration.registration_token});setMessage("Mobile verified. Please login and complete all profile details and upload at least 10 photos.");setTimeout(()=>navigate("/login"),1000)}catch(e){setMessage(errorText(e,"OTP verification failed"))}finally{setBusy(false)}};
 const districts=DISTRICTS[profile.state]||[];
 return <main className="page wide">
  <div className="page-header"><div><h1>Create your matrimonial account</h1><p>Register → verify mobile → login → complete profile → upload 10+ photos → admin approval.</p></div><span className="status">Step {step}/3</span></div>
  {step===1&&<section className="card"><h2>Account</h2><form className="grid-form" onSubmit={register}>
   <label>Mobile number<input name="phone" value={account.phone} onChange={ch(setAccount)} inputMode="tel" pattern="[6-9][0-9]{9}" maxLength="10" required/></label>
   <label>Email<input name="email" type="email" value={account.email} onChange={ch(setAccount)} required/></label>
   <label>Password<input name="password" type="password" value={account.password} onChange={ch(setAccount)} minLength={8} required/></label>
   <label>Confirm password<input name="confirm_password" type="password" value={account.confirm_password} onChange={ch(setAccount)} minLength={8} required/></label>
   <label>Profile for<select name="profile_for" value={account.profile_for} onChange={ch(setAccount)}><option value="self">Myself</option><option value="son">My Son</option><option value="daughter">My Daughter</option><option value="brother">My Brother</option><option value="sister">My Sister</option><option value="relative">A Relative</option></select></label>
   {account.profile_for!=="self"&&<label>Relationship<input name="relationship" value={account.relationship} onChange={ch(setAccount)} required/></label>}
   <label className="full">Registration location<input name="registration_location" value={account.registration_location} onChange={ch(setAccount)} placeholder="City / District / State" required/></label>
   <div className="full"><button disabled={busy}>{busy?"Creating...":"Continue"}</button></div>
  </form></section>}
  {step===2&&<section className="card"><h2>Basic details</h2><p className="muted">These details are required for account activation. You will complete the remaining profile after login.</p><form className="grid-form" onSubmit={saveBasic}>
   <label>Full name<input name="name" value={profile.name} onChange={ch(setProfile)} required/></label>
   <label>Gender<select name="gender" value={profile.gender} onChange={ch(setProfile)} required><option value="">Select</option><option>Male</option><option>Female</option></select></label>
   <label>Date of birth<input type="date" name="date_of_birth" max={minAdultDob()} value={profile.date_of_birth} onChange={ch(setProfile)} required/></label>
   <label>Caste / Community<select name="caste" value={profile.caste} onChange={ch(setProfile)} required><option value="">Select caste / community</option>{CASTES.map(x=><option key={x}>{x}</option>)}</select></label>
   <label>State<select name="state" value={profile.state} onChange={ch(setProfile)} required><option value="">Select state</option>{STATES.map(x=><option key={x}>{x}</option>)}</select></label>
   <label>District<select name="district" value={profile.district} onChange={ch(setProfile)} required disabled={!profile.state}><option value="">Select district</option>{districts.map(x=><option key={x}>{x}</option>)}{profile.state&&districts.length===0&&<option>Other District</option>}</select></label>
   <label>City / Village<input name="city_or_village" value={profile.city_or_village} onChange={ch(setProfile)} placeholder="Enter city or village" required/></label>
   <label className="full">Permanent address<textarea name="permanent_address" value={profile.permanent_address} onChange={ch(setProfile)} required/></label>
   <label className="full">Preferred / looking location<input name="preferred_location" value={profile.preferred_location} onChange={ch(setProfile)} required/></label>
   <div className="full"><button disabled={busy}>{busy?"Saving...":"Save & verify mobile"}</button></div>
  </form></section>}
  {step===3&&<section className="card"><h2>Verify mobile</h2><p>OTP sent to <b>{registration?.otp_contact}</b></p>{registration?.dev_otp&&<p className="dev-otp"><b>Development OTP:</b> {registration.dev_otp}</p>}<form onSubmit={verify}><label>6-digit OTP<input value={otp} onChange={e=>setOtp(e.target.value)} pattern="[0-9]{6}" maxLength={6} required/></label><button disabled={busy}>{busy?"Verifying...":"Verify & Activate"}</button></form></section>}
  {message&&<p className="message">{message}</p>}<p>Already registered? <Link to="/login">Login</Link></p>
 </main>
}
