-- SQL Schema for Nutriken MSK Herbs Database
-- Copy and paste this into the SQL Editor in your Supabase Dashboard

CREATE TABLE IF NOT EXISTS public.msk_herbs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT,
    scientific_name TEXT,
    common_names TEXT[],
    what_is_it TEXT,
    clinical_summary TEXT,
    mechanism_of_action TEXT,
    adverse_reactions TEXT,
    contraindications TEXT,
    dosage TEXT,
    benefits TEXT[],
    drug_interactions TEXT[],
    food_interactions TEXT[],
    side_effects TEXT[],
    warnings TEXT[],
    url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS (Optional, but recommended)
ALTER TABLE public.msk_herbs ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public inserts (needed for the scraper)
CREATE POLICY "Allow public inserts" ON public.msk_herbs FOR INSERT WITH CHECK (true);

-- Create policy to allow public selects (needed for the app)
CREATE POLICY "Allow public select" ON public.msk_herbs FOR SELECT USING (true);
