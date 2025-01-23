import PocketBase from 'pocketbase'

export const pb = new PocketBase('https://auth.casealpha.app');

export async function requestOTP(email: string) {
    return await pb.collection('users').requestOTP(email);
}

export async function verifyOTP(otpId: string, code: string) {
    return await pb.collection('users').authWithOTP(otpId, code);
}

export function logout() {
    pb.authStore.clear();
}

export function isAuthenticated() {
    return pb.authStore.isValid;
}

export function getAuthToken() {
    return pb.authStore.token;
}

export function getUserId() {
    return pb.authStore.model?.id;
}

// Subscribe to auth store changes
pb.authStore.onChange(() => {
    console.log('Auth state changed:', pb.authStore.isValid);
}); 