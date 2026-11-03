-- RapiJob · Ejecutar en Supabase SQL Editor sobre un proyecto nuevo.
create extension if not exists pgcrypto;
create table if not exists public.profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 full_name text not null default '', email text not null unique,
 phone text, role text not null default 'client' check (role in ('client','technician','admin')),
 city text not null default 'Huancayo', district text not null default 'Huancayo',
 avatar_url text, created_at timestamptz not null default now()
);
create table if not exists public.categories (
 id uuid primary key default gen_random_uuid(), name text not null unique,
 slug text not null unique, icon text not null default '🛠️', active boolean not null default true
);
create table if not exists public.technician_profiles (
 user_id uuid primary key references public.profiles(id) on delete cascade,
 headline text not null, description text not null default '', years_experience int not null default 0 check(years_experience>=0),
 base_price numeric(10,2) not null default 0 check(base_price>=0), specialties text[] not null default '{}',
 city text not null default 'Huancayo', district text not null default 'Huancayo',
 latitude double precision, longitude double precision, available boolean not null default true,
 approved boolean not null default false, portfolio_urls text[] not null default '{}', updated_at timestamptz not null default now()
);
create table if not exists public.service_requests (
 id uuid primary key default gen_random_uuid(), client_id uuid not null references public.profiles(id),
 technician_id uuid references public.profiles(id), category_id uuid not null references public.categories(id),
 description text not null, address text not null, city text not null, district text not null,
 latitude double precision not null, longitude double precision not null,
 scheduled_at timestamptz not null, status text not null default 'pending'
 check(status in ('pending','accepted','on_the_way','in_service','completed','cancelled')),
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.request_photos (
 id uuid primary key default gen_random_uuid(), request_id uuid not null references public.service_requests(id) on delete cascade,
 uploaded_by uuid not null references public.profiles(id), storage_path text not null, created_at timestamptz not null default now()
);
create table if not exists public.technician_availability (
 id uuid primary key default gen_random_uuid(), technician_id uuid not null references public.profiles(id) on delete cascade,
 weekday int not null check(weekday between 0 and 6), start_time time not null, end_time time not null,
 active boolean not null default true, check(end_time>start_time)
);
create table if not exists public.reviews (
 id uuid primary key default gen_random_uuid(), request_id uuid not null unique references public.service_requests(id),
 client_id uuid not null references public.profiles(id), technician_id uuid not null references public.profiles(id),
 rating int not null check(rating between 1 and 5), comment text not null default '', created_at timestamptz not null default now()
);
create index if not exists service_requests_client_idx on public.service_requests(client_id,created_at desc);
create index if not exists service_requests_technician_idx on public.service_requests(technician_id,status);
create index if not exists technicians_search_idx on public.technician_profiles(city,approved,available);
create or replace view public.public_technicians as select t.user_id,p.full_name,p.avatar_url,p.phone,p.city as account_city,p.district as account_district,t.headline,t.description,t.years_experience,t.base_price,t.specialties,t.city,t.district,t.latitude,t.longitude,t.available from public.technician_profiles t join public.profiles p on p.id=t.user_id where t.approved=true and t.available=true;
revoke all on public.public_technicians from anon;\ngrant select on public.public_technicians to authenticated;

create or replace function public.is_admin() returns boolean language sql stable security definer set search_path=public
as $$ select exists(select 1 from public.profiles where id=auth.uid() and role='admin') $$;
create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path=public
as $$ begin insert into public.profiles(id,full_name,email,phone) values(new.id,coalesce(new.raw_user_meta_data->>'full_name',''),new.email,new.raw_user_meta_data->>'phone') on conflict(id) do nothing; return new; end $$;
drop trigger if exists on_auth_user_created_rapijob on auth.users;
create trigger on_auth_user_created_rapijob after insert on auth.users for each row execute procedure public.handle_new_user();

alter table public.profiles enable row level security;
alter table public.categories enable row level security;
alter table public.technician_profiles enable row level security;
alter table public.service_requests enable row level security;
alter table public.request_photos enable row level security;
alter table public.technician_availability enable row level security;
alter table public.reviews enable row level security;
create policy "profiles own or admin read" on public.profiles for select using(id=auth.uid() or public.is_admin());
create policy "profiles own client insert" on public.profiles for insert with check(id=auth.uid() and role='client');
create policy "profiles own safe update" on public.profiles for update using(id=auth.uid() and role in ('client','technician')) with check(id=auth.uid() and role in ('client','technician'));
create or replace function public.protect_profile_role() returns trigger language plpgsql security definer set search_path=public as $body$ begin if old.role is distinct from new.role and auth.uid() is not null and not public.is_admin() then raise exception 'Solo administración puede cambiar roles.'; end if; return new; end $body$;
drop trigger if exists protect_profile_role_trigger on public.profiles;
create trigger protect_profile_role_trigger before update on public.profiles for each row execute procedure public.protect_profile_role();
create policy "admin manage profiles" on public.profiles for all using(public.is_admin()) with check(public.is_admin());
create policy "categories public read" on public.categories for select using(active or public.is_admin());
create policy "admin manage categories" on public.categories for all using(public.is_admin()) with check(public.is_admin());
create policy "approved technician directory" on public.technician_profiles for select using(approved=true or user_id=auth.uid() or public.is_admin());
create policy "admin manage technician profiles" on public.technician_profiles for all using(public.is_admin()) with check(public.is_admin());
create policy "technician manage own availability" on public.technician_profiles for update using(user_id=auth.uid() and exists(select 1 from public.profiles where id=auth.uid() and role='technician')) with check(user_id=auth.uid() and exists(select 1 from public.profiles where id=auth.uid() and role='technician'));
create or replace function public.protect_technician_approval() returns trigger language plpgsql security definer set search_path=public as $body$ begin if old.approved is distinct from new.approved and auth.uid() is not null and not public.is_admin() then raise exception 'Solo administración puede aprobar técnicos.'; end if; return new; end $body$;
drop trigger if exists protect_technician_approval_trigger on public.technician_profiles;
create trigger protect_technician_approval_trigger before update on public.technician_profiles for each row execute procedure public.protect_technician_approval();
create policy "clients create own requests" on public.service_requests for insert with check(client_id=auth.uid() and exists(select 1 from public.profiles where id=auth.uid() and role='client') and exists(select 1 from public.technician_profiles t where t.user_id=technician_id and t.approved=true and t.available=true));
create policy "participants or admin read requests" on public.service_requests for select using(client_id=auth.uid() or technician_id=auth.uid() or public.is_admin());
create policy "assigned technician or admin update requests" on public.service_requests for update using(technician_id=auth.uid() or public.is_admin()) with check(technician_id=auth.uid() or public.is_admin());
create policy "client cancel own pending request" on public.service_requests for update using(client_id=auth.uid() and status='pending') with check(client_id=auth.uid() and status='cancelled');
create policy "request participants read photos" on public.request_photos for select using(exists(select 1 from public.service_requests r where r.id=request_id and (r.client_id=auth.uid() or r.technician_id=auth.uid() or public.is_admin())));
create policy "client upload own request photos" on public.request_photos for insert with check(uploaded_by=auth.uid() and exists(select 1 from public.service_requests r where r.id=request_id and r.client_id=auth.uid()));
create policy "technicians read active availability" on public.technician_availability for select using(active or technician_id=auth.uid() or public.is_admin());
create policy "technicians manage own availability" on public.technician_availability for all using(technician_id=auth.uid() and exists(select 1 from public.profiles where id=auth.uid() and role='technician')) with check(technician_id=auth.uid() and exists(select 1 from public.profiles where id=auth.uid() and role='technician'));
create policy "public read reviews" on public.reviews for select using(true);
create policy "client review completed job" on public.reviews for insert with check(client_id=auth.uid() and exists(select 1 from public.service_requests r where r.id=request_id and r.client_id=auth.uid() and r.technician_id=reviews.technician_id and r.status='completed'));
insert into public.categories(name,slug,icon) values
('Electricistas','electricistas','⚡'),('Plomeros','plomeros','🚰'),('Gasfiteros','gasfiteros','🔧'),('Computadoras y laptops','computadoras','💻'),('Celulares','celulares','📱'),('Instaladores','instaladores','🧰'),('Reparaciones del hogar','hogar','🏠'),('Refrigeración','refrigeracion','❄️'),('Pintores','pintores','🎨'),('Carpinteros','carpinteros','🪚'),('Mecánicos','mecanicos','🚗'),('Otros servicios técnicos','otros','🛠️')
on conflict(slug) do nothing;
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types) values('request-photos','request-photos',false,4194304,array['image/jpeg','image/png','image/webp']) on conflict(id) do nothing;
create policy "upload own request folder" on storage.objects for insert to authenticated with check(bucket_id='request-photos' and (storage.foldername(name))[1]=auth.uid()::text);
create policy "read own request folder" on storage.objects for select to authenticated using(bucket_id='request-photos' and (storage.foldername(name))[1]=auth.uid()::text);
-- Después de crear tu cuenta, ejecuta esta instrucción con tu correo para convertirla en administradora:
-- update public.profiles set role='admin' where email='TU_CORREO@EJEMPLO.COM';


-- Habilita actualizaciones en vivo de solicitudes para los paneles conectados.
do $$ begin
  alter publication supabase_realtime add table public.service_requests;
exception when duplicate_object then null;
end $$;

create policy "request participants read uploaded images" on storage.objects for select to authenticated using(
 bucket_id='request-photos' and exists(
  select 1 from public.request_photos p join public.service_requests r on r.id=p.request_id
  where p.storage_path=name and (r.client_id=auth.uid() or r.technician_id=auth.uid() or public.is_admin())
 )
);
