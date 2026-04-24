-- ==========================================
-- SUPABASE STORAGE RLS POLICIES (Secure Setup)
-- Run this in the Supabase Dashboard -> SQL Editor
-- ==========================================

-- 1. Enable RLS on the storage.objects table (if not already enabled)
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- ==========================================
-- BUCKET: uploads
-- ==========================================
-- Allow public viewing of uploads (needed for the frontend to show images)
CREATE POLICY "Public Read: uploads" 
ON storage.objects FOR SELECT 
USING (bucket_id = 'uploads');

-- Allow users to upload ONLY to their own folder (folder name must match their user ID)
CREATE POLICY "Auth Write: uploads" 
ON storage.objects FOR INSERT 
TO authenticated 
WITH CHECK (bucket_id = 'uploads' AND (auth.uid())::text = (storage.foldername(name))[1]);

-- Allow users to delete/update ONLY their own files
CREATE POLICY "Auth Update/Delete: uploads" 
ON storage.objects FOR ALL 
TO authenticated 
USING (bucket_id = 'uploads' AND (auth.uid())::text = (storage.foldername(name))[1]);


-- ==========================================
-- BUCKET: designs
-- ==========================================
-- Allow public viewing of designs
CREATE POLICY "Public Read: designs" 
ON storage.objects FOR SELECT 
USING (bucket_id = 'designs');

-- Allow users to upload ONLY to their own folder
CREATE POLICY "Auth Write: designs" 
ON storage.objects FOR INSERT 
TO authenticated 
WITH CHECK (bucket_id = 'designs' AND (auth.uid())::text = (storage.foldername(name))[1]);

-- Allow users to delete/update ONLY their own files
CREATE POLICY "Auth Update/Delete: designs" 
ON storage.objects FOR ALL 
TO authenticated 
USING (bucket_id = 'designs' AND (auth.uid())::text = (storage.foldername(name))[1]);


-- ==========================================
-- BUCKET: models
-- ==========================================
-- Allow public viewing of 3D models
CREATE POLICY "Public Read: models" 
ON storage.objects FOR SELECT 
USING (bucket_id = 'models');

-- Allow users to upload ONLY to their own folder
CREATE POLICY "Auth Write: models" 
ON storage.objects FOR INSERT 
TO authenticated 
WITH CHECK (bucket_id = 'models' AND (auth.uid())::text = (storage.foldername(name))[1]);

-- Allow users to delete/update ONLY their own files
CREATE POLICY "Auth Update/Delete: models" 
ON storage.objects FOR ALL 
TO authenticated 
USING (bucket_id = 'models' AND (auth.uid())::text = (storage.foldername(name))[1]);

-- Note: The backend uses the Service Role Key, which automatically bypasses RLS.
-- These policies specifically protect the frontend and prevent attackers from
-- using the public API key to upload malicious files or delete other users' files.
