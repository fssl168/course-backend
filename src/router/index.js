// 后端路由配置
// 注意：这是一个示例文件，实际的路由配置在app.py中实现

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/admin.html')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login.html')
  },
  {
    path: '/my-courses',
    name: 'MyCourses',
    component: () => import('../views/my_courses.html')
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/admin.html')
  },
  {
    path: '/admin/users',
    name: 'UserManagement',
    component: () => import('../views/user_management.html')
  }
]

export default routes