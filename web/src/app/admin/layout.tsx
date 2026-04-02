"use client";

import { Layout, Menu } from "antd";
import { usePathname, useRouter } from "next/navigation";
import React from "react";

const { Sider, Content } = Layout;

const menuItems = [
  { key: "/admin/category-rules", label: "Category Rules" },
  { key: "/admin/style-bible", label: "Style Bible" },
  { key: "/admin/wwise-templates", label: "Wwise Templates" },
  { key: "/admin/mappings", label: "Mapping Dictionary" },
  { key: "/admin/qa-rules", label: "QA Rules" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={220} theme="light" style={{ borderRight: "1px solid #f0f0f0" }}>
        <div style={{ padding: "16px", fontWeight: "bold", fontSize: 16 }}>
          Admin Console
        </div>
        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          onClick={({ key }) => router.push(key)}
        />
      </Sider>
      <Content style={{ padding: 24 }}>{children}</Content>
    </Layout>
  );
}
