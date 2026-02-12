import Sidebar from "../components/Sidebar";
import { Outlet } from "react-router-dom";




function Dashboard() {
  return (
    <>
      <Sidebar />
      <div className="dashboard-content">
        <Outlet />
      </div>
    </>
  );
}

export default Dashboard;
