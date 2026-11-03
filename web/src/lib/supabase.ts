import { createClient, SupabaseClient } from '@supabase/supabase-js';
export type PublicConfig={supabaseUrl:string;supabaseAnonKey:string;googleMapsApiKey:string};
export async function loadConfig():Promise<PublicConfig>{const r=await fetch('/config.json');if(!r.ok)throw new Error('No se pudo leer la configuración del servidor.');return r.json();}
let client:SupabaseClient|null=null;
export function supabase(config:PublicConfig){if(!client)client=createClient(config.supabaseUrl,config.supabaseAnonKey,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});return client;}
export type Profile={id:string;full_name:string;email:string;phone:string|null;role:'client'|'technician'|'admin';city:string;district:string;avatar_url:string|null};
export type Category={id:string;name:string;slug:string;icon:string};
export type Job={id:string;description:string;address:string;city:string;district:string;scheduled_at:string;status:string;photos:string[];created_at:string;client_id:string;technician_id:string|null;category_id:string;profiles?:Profile;categories?:Category};
