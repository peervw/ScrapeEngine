import PocketBase from 'pocketbase'

// Initialize PocketBase
export const pb = new PocketBase('https://auth.casealpha.app');

export async function requestOTP(email: string) {
  return await pb.collection('users').requestOTP(email);
}

export async function verifyOTP(otpId: string, code: string) {
  const authData = await pb.collection('users').authWithOTP(otpId, code);
  pb.authStore.save(authData.token, authData.record);
  return authData;
}

export async function signIn(email: string, password: string) {
    const authData = await pb.collection('users').authWithPassword(email, password);
    pb.authStore.save(authData.token, authData.record);
    return authData;
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
  console.log('Auth state changed:', {
    isValid: pb.authStore.isValid,
    token: pb.authStore.token,
    model: pb.authStore.model
  });
});