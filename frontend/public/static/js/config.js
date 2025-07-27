// Supabase configuration
async function getSupabaseConfig() {
    console.log('[Config] Starting to fetch Supabase configuration...');
    try {
        console.log('[Config] Making request to /api/auth/config');
        const response = await fetch('/api/auth/config');
        console.log('[Config] Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch config: ${response.status} ${response.statusText}`);
        }
        
        const config = await response.json();
        console.log('[Config] Configuration loaded successfully:', {
            hasUrl: !!config.supabaseUrl,
            hasKey: !!config.supabaseKey,
            urlDomain: config.supabaseUrl ? new URL(config.supabaseUrl).hostname : null
        });
        
        return {
            url: config.supabaseUrl,
            anonKey: config.supabaseKey
        };
    } catch (error) {
        console.error('[Config] Failed to load Supabase configuration:', error);
        throw error;
    }
}

export default getSupabaseConfig; 