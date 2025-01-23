'use client';

import { useState } from 'react';
import { requestOTP, verifyOTP, signIn } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ExclamationTriangleIcon } from "@radix-ui/react-icons";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    InputOTP,
    InputOTPGroup,
    InputOTPSlot,
} from "@/components/ui/input-otp"

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [otpCode, setOtpCode] = useState('');
    const [otpId, setOtpId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleRequestOTP = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!email) {
            setError('Please enter your email first');
            return;
        }
        setIsLoading(true);
        try {
            const response = await requestOTP(email);
            setOtpId(response.otpId);
            setError(null);
        } catch {
            setError('Failed to send OTP. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handlePasswordLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await signIn(email, password);
            router.push('/'); // Redirect to dashboard after successful login
        } catch {
            setError('Invalid email or password. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerifyOTP = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!otpId) return;
        
        setIsLoading(true);
        try {
            await verifyOTP(otpId, otpCode);
            router.push('/'); // Redirect to dashboard after successful login
        } catch {
            setError('Invalid OTP code. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl text-center">Sign in</CardTitle>
                    <CardDescription className="text-center">
                        Choose your preferred sign in method
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {error && (
                        <Alert variant="destructive" className="mb-4">
                            <ExclamationTriangleIcon className="h-4 w-4" />
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    <Tabs defaultValue="password" className="w-full" onValueChange={(value) => {
                        setError(null);
                        if (value === 'otp' && email) {
                            handleRequestOTP();
                        }
                    }}>
                        <TabsList className="grid w-full grid-cols-2 mb-6">
                            <TabsTrigger value="password">Password</TabsTrigger>
                            <TabsTrigger value="otp">One-Time Code</TabsTrigger>
                        </TabsList>

                        <TabsContent value="password">
                            <form onSubmit={handlePasswordLogin} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email address</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="name@example.com"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        disabled={isLoading}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="password">Password</Label>
                                    <Input
                                        id="password"
                                        type="password"
                                        placeholder="Enter your password"
                                        required
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        disabled={isLoading}
                                    />
                                </div>
                                <Button 
                                    type="submit" 
                                    className="w-full"
                                    disabled={isLoading}
                                >
                                    {isLoading ? "Signing in..." : "Sign in"}
                                </Button>
                            </form>
                        </TabsContent>

                        <TabsContent value="otp">
                            <form onSubmit={otpId ? handleVerifyOTP : handleRequestOTP} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email address</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="name@example.com"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        disabled={isLoading || otpId !== null}
                                    />
                                </div>
                                {otpId ? (
                                    <div className="space-y-2">
                                        <Label htmlFor="otp">Verification Code</Label>
                                        <InputOTP
                                            maxLength={6}
                                            value={otpCode}
                                            onChange={(value: string) => setOtpCode(value)}
                                            disabled={isLoading}
                                        >
                                            <InputOTPGroup>
                                                {Array.from({ length: 6 }).map((_, index) => (
                                                    <InputOTPSlot key={index} index={index} />
                                                ))}
                                            </InputOTPGroup>
                                        </InputOTP>
                                    </div>
                                ) : null}
                                <Button 
                                    type="submit" 
                                    className="w-full"
                                    disabled={isLoading}
                                >
                                    {isLoading 
                                        ? (otpId ? "Verifying..." : "Sending code...") 
                                        : (otpId ? "Verify Code" : "Send Code")}
                                </Button>
                            </form>
                        </TabsContent>
                    </Tabs>
                </CardContent>
            </Card>
        </div>
    );
}