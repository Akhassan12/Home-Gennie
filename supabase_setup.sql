-- Create a table for public profiles
create table profiles (
  id uuid references auth.users not null primary key,
  updated_at timestamp with time zone,
  display_name text,
  avatar_url text
);

-- Set up Row Level Security (RLS)
alter table profiles enable row level security;

create policy "Public profiles are viewable by everyone." on profiles
  for select using (true);

create policy "Users can insert their own profile." on profiles
  for insert with check (auth.uid() = id);

create policy "Users can update own profile." on profiles
  for update using (auth.uid() = id);

-- Create a table for AI generated designs
create table designs (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references auth.users not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  original_image_url text not null,
  generated_image_url text not null,
  style text,
  room_type text,
  prompt_used text
);

-- Set up Row Level Security (RLS)
alter table designs enable row level security;

create policy "Users can view their own designs." on designs
  for select using (auth.uid() = user_id);

create policy "Users can insert their own designs." on designs
  for insert with check (auth.uid() = user_id);

create policy "Users can update their own designs." on designs
  for update using (auth.uid() = user_id);

create policy "Users can delete their own designs." on designs
  for delete using (auth.uid() = user_id);

-- Set up Storage for images
-- Note: Assuming you create two buckets in Supabase Dashboard: 'uploads' and 'designs' Ensure they are public.

-- Create a trigger to automatically create a profile entry when a new user signs up
create function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, new.raw_user_meta_data->>'display_name');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
