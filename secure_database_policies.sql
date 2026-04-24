-- ==========================================
-- SUPABASE DATABASE RLS POLICIES (Secure Setup)
-- Run this in the Supabase Dashboard -> SQL Editor
-- ==========================================

-- Enable Row Level Security on the `designs` table
ALTER TABLE public.designs ENABLE ROW LEVEL SECURITY;

-- 1. Users can ONLY read their own designs
CREATE POLICY "Users can read own designs" 
ON public.designs FOR SELECT 
TO authenticated 
USING (auth.uid() = user_id);

-- 2. Users can ONLY insert designs linked to their own user_id
CREATE POLICY "Users can insert own designs" 
ON public.designs FOR INSERT 
TO authenticated 
WITH CHECK (auth.uid() = user_id);

-- 3. Users can ONLY update their own designs
CREATE POLICY "Users can update own designs" 
ON public.designs FOR UPDATE 
TO authenticated 
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 4. Users can ONLY delete their own designs
CREATE POLICY "Users can delete own designs" 
ON public.designs FOR DELETE 
TO authenticated 
USING (auth.uid() = user_id);

-- Note: The Python backend uses the Service Role Key to insert generated designs.
-- The Service Role Key bypasses RLS, so the backend API will still work normally.
-- These policies prevent malicious users from calling the Supabase API directly
-- from the browser to delete/view other users' data.
