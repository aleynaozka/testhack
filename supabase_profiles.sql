-- Supabase SQL Editor'da çalıştırılacak demo profil tablosu.
-- E-posta sahipliği Supabase Auth confirmation ile doğrulanır.

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  full_name text,
  role text not null check (role in ('student', 'academic', 'industry')),
  industry_type text check (
    industry_type is null or
    industry_type in ('entrepreneur', 'company_without_rd', 'rd_center')
  ),
  verification_status text not null default 'pending'
    check (verification_status in ('pending', 'verified', 'rejected')),
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
on public.profiles for select
using (auth.uid() = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
on public.profiles for update
using (auth.uid() = id)
with check (auth.uid() = id);

-- Kullanıcı kendi rolünü veya onay durumunu değiştiremez.
revoke update on public.profiles from authenticated;
grant update (full_name, industry_type) on public.profiles to authenticated;

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
declare
  requested_role text;
  requested_industry_type text;
begin
  requested_role := coalesce(new.raw_user_meta_data->>'role', 'student');
  requested_industry_type := new.raw_user_meta_data->>'industry_type';

  if requested_role in ('student', 'academic')
     and lower(new.email) !~ '@[^@]+\.edu\.tr$' then
    raise exception 'Student and academic accounts require an .edu.tr email';
  end if;

  insert into public.profiles (
    id, email, full_name, role, industry_type, verification_status
  ) values (
    new.id,
    lower(new.email),
    new.raw_user_meta_data->>'full_name',
    requested_role,
    case when requested_role = 'industry' then requested_industry_type else null end,
    case when requested_role = 'student' then 'verified' else 'pending' end
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();
