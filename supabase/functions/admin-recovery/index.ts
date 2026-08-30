import { createClient } from 'npm:@supabase/supabase-js@2';

const OWNER_EMAIL = 'marinhrodrigo@gmail.com';
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
});
const authPassword = (v: string) => v.length >= 6 ? v : `RcPin#${v}#Fuel`;

async function getAdmin(admin: ReturnType<typeof createClient>) {
  const { data: managers, error } = await admin.schema('fuel').from('managers')
    .select('user_id,name,role,active').eq('role', 'admin').eq('active', true).limit(2);
  if (error) throw new Error(error.message);
  if (!managers || managers.length !== 1) throw new Error('admin_account_not_unique');
  return managers[0];
}

Deno.serve(async (req) => {
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);
  const body = await req.json().catch(() => ({}));
  const action = String(body.action ?? '');
  const url = Deno.env.get('SUPABASE_URL')!;
  const service = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  const anonKey = Deno.env.get('SUPABASE_ANON_KEY')!;
  const admin = createClient(url, service, { auth: { persistSession: false, autoRefreshToken: false } });
  const publicClient = createClient(url, anonKey, { auth: { persistSession: false, autoRefreshToken: false } });

  try {
    const manager = await getAdmin(admin);
    const userId = String(manager.user_id);
    const adminName = String(manager.name ?? 'Administrador Combustível');

    if (action === 'request_recovery') {
      const { data: users, error: listError } = await admin.auth.admin.listUsers({ page: 1, perPage: 1000 });
      if (listError) return json({ error: listError.message }, 500);
      const conflict = users.users.find((u) => String(u.email ?? '').toLowerCase() === OWNER_EMAIL.toLowerCase() && u.id !== userId);
      if (conflict) return json({ error: 'recovery_email_in_use' }, 409);

      const { data: current, error: currentError } = await admin.auth.admin.getUserById(userId);
      if (currentError || !current.user) return json({ error: currentError?.message ?? 'admin_auth_not_found' }, 500);
      if (String(current.user.email ?? '').toLowerCase() !== OWNER_EMAIL.toLowerCase()) {
        const metadata = {
          ...(current.user.user_metadata ?? {}),
          username: 'admin',
          display_name: adminName,
          app: 'fuel',
          managed_by_admin: true,
          role: 'admin',
          recovery_email: OWNER_EMAIL,
          test_account: false,
        };
        const { error: emailError } = await admin.auth.admin.updateUserById(userId, {
          email: OWNER_EMAIL,
          email_confirm: true,
          user_metadata: metadata,
        });
        if (emailError) return json({ error: emailError.message }, 400);
      }

      const now = new Date();
      const expiresAt = new Date(now.getTime() + 3 * 60 * 1000);
      await admin.schema('fuel').from('admin_recovery_challenges')
        .update({ used_at: now.toISOString() }).is('used_at', null);

      const challengeNonce = `supabase_email_otp:${crypto.randomUUID()}`;
      const { data: inserted, error: insertError } = await admin.schema('fuel').from('admin_recovery_challenges')
        .insert({
          code_hash: challengeNonce,
          purpose: 'admin_password_recovery',
          created_at: now.toISOString(),
          expires_at: expiresAt.toISOString(),
          attempts: 0,
          locked_at: null,
        })
        .select('id,expires_at').single();
      if (insertError || !inserted) return json({ error: insertError?.message ?? 'challenge_create_failed' }, 500);

      const { error: otpError } = await publicClient.auth.signInWithOtp({
        email: OWNER_EMAIL,
        options: { shouldCreateUser: false },
      });
      if (otpError) {
        await admin.schema('fuel').from('admin_recovery_challenges').update({ used_at: new Date().toISOString() }).eq('id', inserted.id);
        return json({ error: otpError.message }, 400);
      }

      await admin.schema('fuel').from('audit_log').insert({
        user_id: userId,
        user_name: adminName,
        table_name: 'auth',
        action: 'ADMIN_RECOVERY_CODE_REQUESTED',
        record_id: userId,
        new_data: { recovery_email: OWNER_EMAIL, expires_in_seconds: 180 },
      });

      return json({ ok: true, challenge_id: inserted.id, expires_at: inserted.expires_at, expires_in: 180, recovery_email: OWNER_EMAIL });
    }

    if (action === 'complete_recovery') {
      const challengeId = Number(body.challenge_id);
      const code = String(body.code ?? '').trim();
      const nextPassword = String(body.password ?? '');
      if (!Number.isInteger(challengeId) || challengeId <= 0 || !/^\d{6}$/.test(code) || nextPassword.length < 4) {
        return json({ error: 'invalid_input' }, 400);
      }

      const { data: challenge, error: challengeError } = await admin.schema('fuel').from('admin_recovery_challenges')
        .select('id,expires_at,used_at,attempts,locked_at')
        .eq('id', challengeId).maybeSingle();
      if (challengeError) return json({ error: challengeError.message }, 500);
      if (!challenge || challenge.used_at || new Date(challenge.expires_at).getTime() <= Date.now()) return json({ error: 'recovery_expired' }, 410);
      if (challenge.locked_at || Number(challenge.attempts ?? 0) >= 5) return json({ error: 'recovery_locked' }, 423);

      const { data: verifyData, error: verifyError } = await publicClient.auth.verifyOtp({
        email: OWNER_EMAIL,
        token: code,
        type: 'email',
      });
      if (verifyError || !verifyData.user || verifyData.user.id !== userId) {
        const attempts = Number(challenge.attempts ?? 0) + 1;
        await admin.schema('fuel').from('admin_recovery_challenges').update({
          attempts,
          locked_at: attempts >= 5 ? new Date().toISOString() : null,
        }).eq('id', challengeId);
        return json({ error: 'invalid_recovery_code', attempts_remaining: Math.max(0, 5 - attempts) }, 401);
      }

      const { data: current, error: currentError } = await admin.auth.admin.getUserById(userId);
      if (currentError || !current.user) return json({ error: currentError?.message ?? 'admin_auth_not_found' }, 500);
      const metadata = {
        ...(current.user.user_metadata ?? {}),
        username: 'admin',
        display_name: adminName,
        app: 'fuel',
        managed_by_admin: true,
        role: 'admin',
        recovery_email: OWNER_EMAIL,
        test_account: false,
      };
      const { error: updateError } = await admin.auth.admin.updateUserById(userId, {
        email: OWNER_EMAIL,
        email_confirm: true,
        password: authPassword(nextPassword),
        user_metadata: metadata,
        ban_duration: 'none',
      });
      if (updateError) return json({ error: updateError.message }, 400);

      await admin.schema('fuel').from('active_sessions').delete().eq('user_id', userId);
      await admin.schema('fuel').from('session_revocations').delete().eq('user_id', userId);
      await admin.schema('fuel').from('unit_assignments').delete().eq('user_id', userId);
      await admin.schema('fuel').from('admin_recovery_challenges').update({ used_at: new Date().toISOString(), used_by: userId }).eq('id', challengeId);
      await admin.schema('fuel').from('audit_log').insert({
        user_id: userId,
        user_name: adminName,
        table_name: 'auth',
        action: 'ADMIN_PASSWORD_RECOVERY',
        record_id: userId,
        new_data: { recovery_email: OWNER_EMAIL, source: 'v37_email_otp_3m' },
      });

      return json({ ok: true, username: 'admin', recovery_email: OWNER_EMAIL });
    }

    return json({ error: 'unknown_action' }, 400);
  } catch (e) {
    return json({ error: e instanceof Error ? e.message : String(e) }, 500);
  }
});
