-- ================================================================
-- Cold Email Engine — Supabase Schema
-- Run this entire file in:
-- Supabase Dashboard → SQL Editor → New query → paste → Run
-- ================================================================
-- This file is not used by the application at runtime.
-- ==================================================================

-- ── TABLE: user_preferences ─────────────────────────────────────
-- One row per user. Stores sidebar defaults and paid/free status.

CREATE TABLE IF NOT EXISTS public.user_preferences (
    user_id        UUID        PRIMARY KEY
                               REFERENCES auth.users(id) ON DELETE CASCADE,
    offer_text     TEXT,
    default_tone   TEXT        NOT NULL DEFAULT 'direct',
    default_length TEXT        NOT NULL DEFAULT 'short (5-6 lines)',
    is_paid        BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ── TABLE: saved_templates ──────────────────────────────────────
-- One row per saved email. Stores the full pipeline output.

CREATE TABLE IF NOT EXISTS public.saved_templates (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID        NOT NULL
                               REFERENCES auth.users(id) ON DELETE CASCADE,
    name           TEXT        NOT NULL,
    prospect_name  TEXT,
    company_name   TEXT,
    role           TEXT,
    hook           TEXT,
    email_body     TEXT        NOT NULL,
    followup_1     TEXT,
    followup_2     TEXT,
    subjects       JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ── TABLE: usage_log ────────────────────────────────────────────
-- One row per user per calendar day. Resets automatically each day.

CREATE TABLE IF NOT EXISTS public.usage_log (
    id               UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID    NOT NULL
                             REFERENCES auth.users(id) ON DELETE CASCADE,
    log_date         DATE    NOT NULL DEFAULT CURRENT_DATE,
    emails_generated INTEGER NOT NULL DEFAULT 0,
    UNIQUE (user_id, log_date)
);


-- ================================================================
-- ROW LEVEL SECURITY
-- Each user can only read and write their own rows.
-- Without this, any authenticated user can query everyone's data.
-- ================================================================

ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_templates   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_log         ENABLE ROW LEVEL SECURITY;


-- ── user_preferences policies ───────────────────────────────────

CREATE POLICY "select_own_preferences" ON public.user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "insert_own_preferences" ON public.user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "update_own_preferences" ON public.user_preferences
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- ── saved_templates policies ────────────────────────────────────

CREATE POLICY "select_own_templates" ON public.saved_templates
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "insert_own_templates" ON public.saved_templates
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "delete_own_templates" ON public.saved_templates
    FOR DELETE USING (auth.uid() = user_id);


-- ── usage_log policies ──────────────────────────────────────────

CREATE POLICY "select_own_usage" ON public.usage_log
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "insert_own_usage" ON public.usage_log
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "update_own_usage" ON public.usage_log
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- ================================================================
-- AUTO-UPDATE updated_at ON user_preferences
-- ================================================================

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_user_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();