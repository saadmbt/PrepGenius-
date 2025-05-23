import React from 'react'
import { NavLink, useLocation } from 'react-router-dom';
import UpgradePlanCard from './UpgradePlanCard';
import {navigationItems} from '../../constants/index'
import Logo from '../../assets/authnavbarlogo.png'
import { SidebarClose } from 'lucide-react';
function Sidebar({isSidebarOpen,onClose,toggleSidebar}) {
  console.log(isSidebarOpen)
  const location = useLocation();

  return (
    <>
        {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={toggleSidebar}
        />
      )}
      {/* Sidebar */}
    <aside className={`
      fixed md:sticky top-0 left-0 h-screen w-64 bg-white  shadow-lg flex flex-col z-50
      transform transition-transform duration-200 ease-in-out
      ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
    `}>
      <div className="p-6 flex items-end ">
          <img src={Logo} className="h-14 w-48" />
         <button 
              className="text-gray-600 mb-4  md:hidden"
              onClick={toggleSidebar}
          >
              <SidebarClose className="h-6 w-6" />
          </button>
      </div>
      {/* Navigation */}
      <nav className="mt-4 flex-1 overflow-y-auto">
        {navigationItems.map((item) => (
          <NavLink
            key={item.label}
            to={item.to}
            onClick={() => onClose()}
            className={({ isActive }) => `
              flex items-center px-6 py-3 text-gray-700  
              hover:bg-blue-50  transition-colors duration-200
              ${isActive && 
                ((item.exact && location.pathname === item.to) || 
                 (!item.exact && location.pathname.startsWith(item.to)))
                ? 'bg-blue-50 border-r-4 border-blue-500' 
                : ''}
            `}
          >
            <item.icon className="h-5 w-5 mr-3" />
            {item.label}
          </NavLink>
        ))}
      </nav>
        {/* Upgrade Plan Card */}
        <UpgradePlanCard />
      </aside>
    </>
    
  )
}

export default Sidebar
