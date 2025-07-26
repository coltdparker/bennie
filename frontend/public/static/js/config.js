// Supabase configuration
async function getSupabaseConfig() {
    try {
        const response = await fetch('/api/auth/config');
        const config = await response.json();
        return {
            url: config.supabaseUrl,
            anonKey: config.supabaseKey
        };
    } catch (error) {
        console.error('Failed to load Supabase configuration:', error);
        throw error;
    }
}

export default getSupabaseConfig; 