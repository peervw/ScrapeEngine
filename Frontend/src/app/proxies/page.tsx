"use client"

import React, { useEffect, useState, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Loader2, RefreshCcw, Trash2, Eye, EyeOff } from "lucide-react";
import { api } from '@/lib/api';
import type { ProxyStats, ProxyCreate } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { useToast } from "@/components/ui/use-toast";
import { Copy, Check } from "lucide-react";

interface CopiedStates {
  [key: string]: boolean;
}

const ProxiesPage: React.FC = () => {
  const [proxies, setProxies] = useState<ProxyStats[]>([]);
  const [totalProxies, setTotalProxies] = useState(0);
  const [availableProxies, setAvailableProxies] = useState(0);
  const [isLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedStates, setCopiedStates] = useState<CopiedStates>({});
  const { toast } = useToast();

  // Dialog states
  const [addProxyOpen, setAddProxyOpen] = useState(false);
  const [webshareOpen, setWebshareOpen] = useState(false);
  const [newProxy, setNewProxy] = useState<ProxyCreate>({
    host: '',
    port: '',
    username: '',
    password: '',
  });
  const [bulkProxies, setBulkProxies] = useState('');
  const [webshareToken, setWebshareToken] = useState('');
  const [currentWebshareToken, setCurrentWebshareToken] = useState<string | null>(null);
  const [showToken, setShowToken] = useState(false);
  const [isDeleteAllConfirmOpen, setIsDeleteAllConfirmOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleCopy = async (text: string, key: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedStates((prev: CopiedStates) => ({ ...prev, [key]: true }));
    setTimeout(() => setCopiedStates((prev: CopiedStates) => ({ ...prev, [key]: false })), 2000);
    toast({
      title: "Copied",
      description: "Text copied to clipboard",
      duration: 2000,
    });
  };

  const loadProxies = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const response = await api.getProxies();
      setProxies(response.proxies);
      setTotalProxies(response.total_proxies);
      setAvailableProxies(response.available_proxies);
      setError(null);
    } catch (err) {
      setError('Failed to load proxies');
      console.error('Error loading proxies:', err);
      toast({
        title: "Error",
        description: "Failed to load proxies",
        variant: "destructive",
        duration: 3000,
      });
    } finally {
      setIsRefreshing(false);
    }
  }, [toast]);

  useEffect(() => {
    loadProxies();
    const interval = setInterval(loadProxies, 30000);
    return () => clearInterval(interval);
  }, [loadProxies]);

  const handleAddProxy = async () => {
    try {
      await api.addProxy(newProxy);
      setAddProxyOpen(false);
      setNewProxy({ host: '', port: '', username: '', password: '' });
      loadProxies();
      toast({
        title: "Success",
        description: "Proxy added successfully",
        duration: 3000,
      });
    } catch (err) {
      setError('Failed to add proxy');
      console.error('Error adding proxy:', err);
      toast({
        title: "Error",
        description: "Failed to add proxy",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const handleBulkImport = async () => {
    try {
      const lines = bulkProxies.split('\n').filter(line => line.trim());
      for (const line of lines) {
        const parts = line.split('@');
        if (parts.length === 0) continue;

        let host: string, port: string, username: string | undefined, password: string | undefined;

        if (parts.length === 2) {
          // Format: username:password@host:port
          const [userPass, hostPort] = parts;
          [username, password] = userPass.split(':');
          [host, port] = hostPort.split(':');
        } else {
          // Format: host:port
          [host, port] = parts[0].split(':');
        }

        if (host && port) {
          await api.addProxy({ host, port, username, password });
        }
      }
      setAddProxyOpen(false);
      setBulkProxies('');
      loadProxies();
    } catch (error: unknown) {
      setError('Failed to import proxies');
      console.error('Error importing proxies:', error);
    }
  };

  const handleDeleteProxy = async (host: string) => {
    try {
      await api.deleteProxy(host);
      loadProxies();
      toast({
        title: "Success",
        description: "Proxy deleted successfully",
        duration: 3000,
      });
    } catch (err) {
      console.error('Error deleting proxy:', err);
      toast({
        title: "Error",
        description: "Failed to delete proxy",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const handleSetWebshareToken = async () => {
    try {
      await api.setWebshareToken(webshareToken);
      setWebshareOpen(false);
      setWebshareToken('');
      loadWebshareToken();
      toast({
        title: "Success",
        description: "Webshare token set successfully",
        duration: 3000,
      });
    } catch (err) {
      console.error('Error setting webshare token:', err);
      toast({
        title: "Error",
        description: "Failed to set webshare token",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const handleClearWebshareToken = async () => {
    try {
      await api.setWebshareToken('');
      setCurrentWebshareToken(null);
      toast({
        title: "Success",
        description: "Webshare token cleared successfully",
        duration: 3000,
      });
    } catch (err) {
      console.error('Error clearing webshare token:', err);
      toast({
        title: "Error",
        description: "Failed to clear webshare token",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const loadWebshareToken = async () => {
    try {
      const settings = await api.getSettings();
      const token = settings.webshare_token;
      setCurrentWebshareToken(token || null);
      setError(null);
    } catch (err) {
      setError('Failed to load Webshare token');
      console.error('Error loading Webshare token:', err);
    }
  };

  useEffect(() => {
    loadWebshareToken();
  }, []);

  const handleRefreshProxies = async () => {
    try {
      await api.refreshProxies();
      loadProxies();
      toast({
        title: "Success",
        description: "Proxies refreshed successfully",
        duration: 3000,
      });
    } catch (err) {
      console.error('Error refreshing proxies:', err);
      toast({
        title: "Error",
        description: "Failed to refresh proxies",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const handleDeleteAllProxies = async () => {
    try {
      // Delete all proxies one by one
      for (const proxy of proxies) {
        await api.deleteProxy(proxy.host);
      }
      setIsDeleteAllConfirmOpen(false);
      loadProxies();
      toast({
        title: "Success",
        description: "All proxies deleted successfully",
        duration: 3000,
      });
    } catch (err) {
      console.error('Error deleting all proxies:', err);
      toast({
        title: "Error",
        description: "Failed to delete all proxies",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Proxies</h1>
        <div className="flex items-center gap-4">
          <Button onClick={() => setAddProxyOpen(true)}>
            Add Proxy
          </Button>
          <Button variant="outline" onClick={() => setWebshareOpen(true)}>
            Set Webshare Token
          </Button>
          <Button 
            variant="outline" 
            onClick={() => setIsDeleteAllConfirmOpen(true)}
            className="text-destructive hover:text-destructive/90"
          >
            Delete All
          </Button>
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefreshProxies}
            disabled={isLoading}
          >
            <RefreshCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-md">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Proxies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground mb-4">
            Total Proxies: {totalProxies} | Available Proxies: {availableProxies}
          </div>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Host</TableHead>
                  <TableHead>Port</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead>Success Rate</TableHead>
                  <TableHead>Avg Response Time</TableHead>
                  <TableHead>Failures</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : proxies.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                      No proxies available
                    </TableCell>
                  </TableRow>
                ) : (
                  proxies.map((proxy) => (
                    <TableRow key={proxy.host} className={isRefreshing ? "opacity-50 transition-opacity" : ""}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {proxy.host}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleCopy(`${proxy.host}:${proxy.port}`, `proxy-${proxy.host}`)}
                            className="h-4 w-4 p-0"
                          >
                            {copiedStates[`proxy-${proxy.host}`] ? (
                              <Check className="h-3 w-3" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>{proxy.port}</TableCell>
                      <TableCell>
                        {proxy.last_used
                          ? formatDistanceToNow(new Date(proxy.last_used), {
                              addSuffix: true,
                            })
                          : 'Never'}
                      </TableCell>
                      <TableCell>{(proxy.success_rate * 100).toFixed(1)}%</TableCell>
                      <TableCell>
                        {proxy.avg_response_time
                          ? `${proxy.avg_response_time.toFixed(2)}s`
                          : 'N/A'}
                      </TableCell>
                      <TableCell>{proxy.failures}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteProxy(proxy.host)}
                            disabled={isLoading}
                            className="text-destructive hover:text-destructive/90 h-8 w-8"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Add Proxy Dialog */}
      <Dialog open={addProxyOpen} onOpenChange={setAddProxyOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add Proxy</DialogTitle>
          </DialogHeader>
          <Tabs defaultValue="single">
            <TabsList>
              <TabsTrigger value="single">Single Proxy</TabsTrigger>
              <TabsTrigger value="bulk">Bulk Import</TabsTrigger>
            </TabsList>
            <TabsContent value="single" className="space-y-4">
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="host">Host</Label>
                  <Input
                    id="host"
                    value={newProxy.host}
                    onChange={(e) => setNewProxy({ ...newProxy, host: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="port">Port</Label>
                  <Input
                    id="port"
                    value={newProxy.port}
                    onChange={(e) => setNewProxy({ ...newProxy, port: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="username">Username (optional)</Label>
                  <Input
                    id="username"
                    value={newProxy.username || ''}
                    onChange={(e) => setNewProxy({ ...newProxy, username: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="password">Password (optional)</Label>
                  <Input
                    id="password"
                    type="password"
                    value={newProxy.password || ''}
                    onChange={(e) => setNewProxy({ ...newProxy, password: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setAddProxyOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddProxy}>Add</Button>
              </DialogFooter>
            </TabsContent>
            <TabsContent value="bulk" className="space-y-4">
              <div className="grid gap-2">
                <Label>
                  Bulk Import (one proxy per line)
                  <div className="text-sm text-muted-foreground mt-1">
                    Format: host:port or username:password@host:port
                  </div>
                </Label>
                <Textarea
                  placeholder="proxy1.example.com:8080&#10;user:pass@proxy2.example.com:8080"
                  value={bulkProxies}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setBulkProxies(e.target.value)}
                  rows={10}
                />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setAddProxyOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleBulkImport}>Import</Button>
              </DialogFooter>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* Webshare Token Dialog */}
      <Dialog open={webshareOpen} onOpenChange={setWebshareOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Webshare API Token</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {currentWebshareToken && (
              <div className="space-y-2">
                <Label>Current Token</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type={showToken ? "text" : "password"}
                    value={currentWebshareToken}
                    readOnly
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowToken(!showToken)}
                  >
                    {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                  <Button
                    variant="destructive"
                    size="icon"
                    onClick={handleClearWebshareToken}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
            <div className="grid gap-2">
              <Label htmlFor="token">New API Token</Label>
              <Input
                id="token"
                type="password"
                value={webshareToken}
                onChange={(e) => setWebshareToken(e.target.value)}
                placeholder={currentWebshareToken ? "Enter new token to update" : "Enter Webshare API token"}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setWebshareOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSetWebshareToken}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete All Confirmation Dialog */}
      <Dialog open={isDeleteAllConfirmOpen} onOpenChange={setIsDeleteAllConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete All Proxies</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            Are you sure you want to delete all proxies? This action cannot be undone.
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteAllConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteAllProxies}>
              Delete All
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProxiesPage; 