import React, { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, Typography, theme } from 'antd'
import {
  DashboardOutlined,
  AppstoreOutlined,
  InboxOutlined,
  ToolOutlined,
  ShoppingCartOutlined,
} from '@ant-design/icons'

const { Sider, Content } = AntLayout
const { Title } = Typography

const menuItems = [
  { key: '/dashboard',  icon: <DashboardOutlined />,  label: 'Dashboard' },
  { key: '/products',  icon: <AppstoreOutlined />,  label: 'Products' },
  { key: '/inventory',  icon: <InboxOutlined />,     label: 'Inventory' },
  { key: '/purchasing',icon: <ShoppingCartOutlined />, label: 'Purchasing' },
  { key: '/manufacturing', icon: <ToolOutlined />,    label: 'Manufacturing' },
  { key: '/sales',    icon: <ShoppingCartOutlined />, label: 'Sales' },
]

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()

  const selectedKey = '/' + location.pathname.split('/')[1]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          background: token.colorBgContainer,
          borderRight: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <Title
            level={4}
            style={{ margin: 0, color: token.colorPrimary, whiteSpace: 'nowrap' }}
          >
            {collapsed ? 'HOS' : 'HOS ERP'}
          </Title>
        </div>

        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, marginTop: 8 }}
        />
      </Sider>

      <AntLayout>
        <Content
          style={{
            padding: 24,
            minHeight: 280,
            background: token.colorBgLayout,
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}