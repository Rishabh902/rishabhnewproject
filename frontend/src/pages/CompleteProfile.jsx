import {useEffect,useState} from "react";
import api,{mediaUrl} from "../api/client";
import {STATES,DISTRICTS,CASTES,DEGREES,INCOME_RANGES,PROFESSIONS} from "../data/options";

const empty={name:"",gender:"",date_of_birth:"",caste:"",community:"",gothra:"",education:"",degree:"",profession:"",income:"",height_cm:"",weight_kg:"",state:"",district:"",city_or_village:"",permanent_address:"",preferred_location:"",family_details:""};
const prefEmpty={min_age:"",max_age:"",min_height_cm:"",max_height_cm:"",income:"",education:"",profession:"",location:"",community:"",other_criteria:""};
const errorText=e=>{const d=e.response?.data?.detail;if(typeof d==="string")return d;if(Array.isArray(d))return d.map(x=>x.msg).join(", ");return d?.message||"Something went wrong"};
function dobMax(){const d=new Date();d.setFullYear(d.getFullYear()-18);return d.toISOString().slice(0,10)}

export default function CompleteProfile(){
 const [profile,setProfile]=useState(empty),[prefs,setPrefs]=useState(prefEmpty),[photos,setPhotos]=useState([]),[files,setFiles]=useState([]),[status,setStatus]=useState(""),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false);
 const load=()=>Promise.all([api.get("/api/profiles/me"),api.get("/api/profiles/me/preferences"),api.get("/api/profiles/me/photos")]).then(([p,r,m])=>{setProfile({...empty,...p.data});setPrefs({...prefEmpty,...(r.data||{})});setPhotos(m.data.photos||[])}).catch(e=>setStatus(errorText(e))).finally(()=>setLoading(false));
 useEffect(()=>{load()},[]);
 const change=(setter)=>(e)=>setter(v=>({...v,[e.target.name]:e.target.value}));
 const save=async e=>{e.preventDefault();setBusy(true);setStatus("");try{const payload={...profile,height_cm:Number(profile.height_cm),weight_kg:Number(profile.weight_kg)};const {data}=await api.put("/api/profiles/me",payload);setProfile({...empty,...data});setStatus("All profile details saved.")}catch(e){setStatus(errorText(e))}finally{setBusy(false)}};
 const savePrefs=async e=>{e.preventDefault();setBusy(true);try{await api.put("/api/profiles/me/preferences",Object.fromEntries(Object.entries(prefs).map(([k,v])=>[k,["min_age","max_age","min_height_cm","max_height_cm"].includes(k)?(v?Number(v):null):v])));setStatus("Partner preferences saved.")}catch(e){setStatus(errorText(e))}finally{setBusy(false)}};
 const upload=async()=>{if(!files.length)return;setBusy(true);setStatus("Uploading photos...");try{const fd=new FormData();files.forEach(f=>fd.append("files",f));await api.post("/api/profiles/me/photos",fd);setFiles([]);setStatus("Photos uploaded successfully.");await load()}catch(e){setStatus(errorText(e))}finally{setBusy(false)}};
 const remove=async id=>{setBusy(true);try{await api.delete(`/api/profiles/me/photos/${id}`);await load()}catch(e){setStatus(errorText(e))}finally{setBusy(false)}};
 const submit=async()=>{setBusy(true);setStatus("Submitting for admin review...");try{const {data}=await api.post("/api/profiles/me/complete");setProfile(p=>({...p,...data}));setStatus("Profile submitted for admin approval.")}catch(e){setStatus(errorText(e))}finally{setBusy(false)}};
 if(loading)return <main className="page"><p>Loading...</p></main>;
 const locked=["PENDING_REVIEW","ACTIVE"].includes(profile.status); const districts=DISTRICTS[profile.state]||[];
 return <main className="page wide"><div className="page-header"><div><h1>Complete your profile</h1><p>Every field is required. Upload at least 10 photos before submitting.</p></div><span className={`status ${profile.status?.toLowerCase()}`}>{profile.status}</span></div>
 {profile.rejection_reason&&<section className="card notice"><b>Admin feedback</b><p>{profile.rejection_reason}</p></section>}
 <section className="card"><h2>Personal & matrimonial details</h2><form className="grid-form" onSubmit={save}>
  <label>Full name<input name="name" value={profile.name} onChange={change(setProfile)} required disabled={locked}/></label>
  <label>Gender<select name="gender" value={profile.gender} onChange={change(setProfile)} required disabled={locked}><option value="">Select</option><option>Male</option><option>Female</option></select></label>
  <label>Date of birth<input type="date" name="date_of_birth" max={dobMax()} value={profile.date_of_birth||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <label>Caste / Community<select name="caste" value={profile.caste||""} onChange={change(setProfile)} required disabled={locked}><option value="">Select caste / community</option>{CASTES.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>Community / sub-community<input name="community" value={profile.community||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <label>Gothra / family lineage<input name="gothra" value={profile.gothra||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <label>Education level<select name="education" value={profile.education||""} onChange={change(setProfile)} required disabled={locked}><option value="">Select</option>{DEGREES.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>Degree / qualification<select name="degree" value={profile.degree||""} onChange={change(setProfile)} required disabled={locked}><option value="">Select degree</option>{DEGREES.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>Profession<select name="profession" value={profile.profession||""} onChange={change(setProfile)} required disabled={locked}><option value="">Select profession</option>{PROFESSIONS.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>Annual income<select name="income" value={profile.income||""} onChange={change(setProfile)} required disabled={locked}><option value="">Select income</option>{INCOME_RANGES.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>Height (cm)<input type="number" name="height_cm" min="80" max="250" value={profile.height_cm||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <label>Weight (kg)<input type="number" name="weight_kg" min="20" max="250" value={profile.weight_kg||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <label>State<select name="state" value={profile.state||""} onChange={e=>{change(setProfile)(e);setProfile(v=>({...v,district:""}))}} required disabled={locked}><option value="">Select state</option>{STATES.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>District<select name="district" value={profile.district||""} onChange={change(setProfile)} required disabled={locked||!profile.state}><option value="">Select district</option>{districts.map(x=><option key={x}>{x}</option>)}{!districts.length&&profile.state&&<option>Other District</option>}</select></label>
  <label>City / Village<input name="city_or_village" value={profile.city_or_village||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <label className="full">Permanent address<textarea name="permanent_address" value={profile.permanent_address||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <label className="full">Preferred / looking location<input name="preferred_location" value={profile.preferred_location||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <label className="full">Family details<textarea name="family_details" value={profile.family_details||""} onChange={change(setProfile)} required disabled={locked}/></label>
  <div className="full"><button disabled={busy||locked}>{locked?"Profile locked after submission":"Save all profile details"}</button></div>
 </form></section>
 <section className="card"><h2>Partner preferences</h2><form className="grid-form" onSubmit={savePrefs}>
  <label>Minimum age<input type="number" name="min_age" min="18" max="100" value={prefs.min_age||""} onChange={change(setPrefs)} required disabled={locked}/></label>
  <label>Maximum age<input type="number" name="max_age" min="18" max="100" value={prefs.max_age||""} onChange={change(setPrefs)} required disabled={locked}/></label>
  <label>Minimum height (cm)<input type="number" name="min_height_cm" min="80" max="250" value={prefs.min_height_cm||""} onChange={change(setPrefs)} required disabled={locked}/></label>
  <label>Maximum height (cm)<input type="number" name="max_height_cm" min="80" max="250" value={prefs.max_height_cm||""} onChange={change(setPrefs)} required disabled={locked}/></label>
  <label>Preferred income<select name="income" value={prefs.income||""} onChange={change(setPrefs)} required disabled={locked}><option value="">Select</option>{INCOME_RANGES.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>Preferred education<select name="education" value={prefs.education||""} onChange={change(setPrefs)} required disabled={locked}><option value="">Select</option>{DEGREES.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>Preferred profession<select name="profession" value={prefs.profession||""} onChange={change(setPrefs)} required disabled={locked}><option value="">Select</option>{PROFESSIONS.map(x=><option key={x}>{x}</option>)}</select></label>
  <label>Preferred location<input name="location" value={prefs.location||""} onChange={change(setPrefs)} required disabled={locked}/></label>
  <label>Preferred community<select name="community" value={prefs.community||""} onChange={change(setPrefs)} required disabled={locked}><option value="">Any / select</option>{CASTES.map(x=><option key={x}>{x}</option>)}</select></label>
  <label className="full">Other criteria<textarea name="other_criteria" value={prefs.other_criteria||""} onChange={change(setPrefs)} disabled={locked}/></label>
  <div className="full"><button disabled={busy||locked}>Save partner preferences</button></div>
 </form></section>
 <section className="card"><h2>Photos — minimum 10, maximum 20</h2><p className={photos.length>=10?"message":"error"}>{photos.length}/10 minimum photos uploaded</p>
  <input type="file" accept="image/jpeg,image/png,image/webp" multiple disabled={locked||busy} onChange={e=>setFiles(Array.from(e.target.files||[]))}/>
  {files.length>0&&<p>{files.length} new photo(s) selected.</p>}<button className="secondary" onClick={upload} disabled={!files.length||busy||locked}>Upload selected photos</button>
  <div className="photo-grid">{photos.map(p=><div className="photo-card" key={p.id}><img src={mediaUrl(p.url)} alt="Profile"/><small>{p.is_primary?"Primary photo":""}</small>{!locked&&<button type="button" className="secondary" onClick={()=>remove(p.id)}>Delete</button>}</div>)}</div>
 </section>
 <section className="card"><h2>Submit for admin approval</h2><p>Submission requires every profile field, partner preferences, mobile verification and at least 10 photos.</p><button onClick={submit} disabled={busy||locked}>{profile.status==="PENDING_REVIEW"?"Waiting for admin review":profile.status==="ACTIVE"?"Profile approved":"Submit complete profile"}</button></section>
 {status&&<p className="message">{status}</p>}
 </main>
}
