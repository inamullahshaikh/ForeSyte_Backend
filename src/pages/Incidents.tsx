import { useState, useRef, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from "../components/Header";
import { Search, Filter, MoreVertical, ChevronLeft, ChevronRight } from 'lucide-react';
import { apiService } from '../services/api';

interface Incident {
  id: string;
  camera_id?: string;
  cameraId?: string;
  student_id?: string;
  student_name?: string;
  student?: {
    name: string;
    id: string;
  };
  exam_id?: string;
  exam_name?: string;
  instructor?: string;
  exam?: {
    name: string;
    instructor: string;
  };
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  status: 'investigating' | 'resolved' | 'dismissed';
  confidence: number;
}

const mockIncidents: Incident[] = [
  {
    id: 'INC-001',
    cameraId: 'CAM-A101-02',
    student: { name: 'Sarah Johnson', id: 'STU-2024-001' },
    exam: { name: 'Advanced Mathematics', instructor: 'Dr. Smith' },
    type: 'Suspicious Movement',
    severity: 'medium',
    timestamp: '2024-01-15 10:23:15',
    status: 'investigating',
    confidence: 87
  },
  {
    id: 'INC-002',
    cameraId: 'CAM-B205-01',
    student: { name: 'Mike Chen', id: 'STU-2024-045' },
    exam: { name: 'Computer Science', instructor: 'Prof. Wilson' },
    type: 'Device Detected',
    severity: 'high',
    timestamp: '2024-01-15 14:45:32',
    status: 'investigating',
    confidence: 94
  },
  {
    id: 'INC-003',
    cameraId: 'CAM-C150-03',
    student: { name: 'Emily Davis', id: 'STU-2024-022' },
    exam: { name: 'Physics', instructor: 'Dr. Brown' },
    type: 'Looking Away',
    severity: 'low',
    timestamp: '2024-01-14 11:12:08',
    status: 'dismissed',
    confidence: 72
  },
  {
    id: 'INC-004',
    cameraId: 'CAM-D101-01',
    student: { name: 'Alex Thompson', id: 'STU-2024-089' },
    exam: { name: 'Chemistry', instructor: 'Prof. Davis' },
    type: 'Invigilator Inactive',
    severity: 'medium',
    timestamp: '2024-01-14 15:30:45',
    status: 'resolved',
    confidence: 91
  },
  {
    id: 'INC-005',
    cameraId: 'CAM-A103-04',
    student: { name: 'Rachel Kim', id: 'STU-2024-102' },
    exam: { name: 'Biology', instructor: 'Dr. Martinez' },
    type: 'Multiple Persons',
    severity: 'high',
    timestamp: '2024-01-15 09:15:22',
    status: 'investigating',
    confidence: 96
  },
  {
    id: 'INC-006',
    cameraId: 'CAM-B202-03',
    student: { name: 'James Wilson', id: 'STU-2024-067' },
    exam: { name: 'Economics', instructor: 'Prof. Anderson' },
    type: 'Audio Detected',
    severity: 'medium',
    timestamp: '2024-01-15 13:20:18',
    status: 'resolved',
    confidence: 88
  },
  {
    id: 'INC-007',
    cameraId: 'CAM-C160-02',
    student: { name: 'Sofia Garcia', id: 'STU-2024-034' },
    exam: { name: 'Statistics', instructor: 'Dr. Lee' },
    type: 'Suspicious Movement',
    severity: 'low',
    timestamp: '2024-01-14 16:45:30',
    status: 'dismissed',
    confidence: 76
  },
  {
    id: 'INC-008',
    cameraId: 'CAM-D105-01',
    student: { name: 'Daniel Park', id: 'STU-2024-156' },
    exam: { name: 'Linear Algebra', instructor: 'Prof. White' },
    type: 'Device Detected',
    severity: 'high',
    timestamp: '2024-01-15 11:05:40',
    status: 'investigating',
    confidence: 93
  }
];

interface FilterOptions {
  severity: string[];
  status: string[];
  type: string[];
}

const Incidents = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [activeFilters, setActiveFilters] = useState<FilterOptions>({
    severity: [],
    status: [],
    type: []
  });
  const [showDropdown, setShowDropdown] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const filterRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchIncidents();
  }, [currentPage, activeFilters]);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const severity = activeFilters.severity.length > 0 ? activeFilters.severity[0] : undefined;
      const status = activeFilters.status.length > 0 ? activeFilters.status[0] : undefined;
      
      const response = await apiService.getIncidents({
        severity,
        status,
        page: currentPage,
        limit: 20,
      });

      if (response.data) {
        const incidentsData = response.data.incidents || [];
        // Normalize the data structure
        const normalizedIncidents = incidentsData.map((inc: any) => ({
          id: inc.id,
          camera_id: inc.camera_id,
          cameraId: inc.camera_id || inc.cameraId,
          student_id: inc.student_id,
          student_name: inc.student_name,
          student: inc.student || (inc.student_name ? { name: inc.student_name, id: inc.student_id } : undefined),
          exam_id: inc.exam_id,
          exam_name: inc.exam_name,
          instructor: inc.instructor,
          exam: inc.exam || (inc.exam_name ? { name: inc.exam_name, instructor: inc.instructor || 'N/A' } : undefined),
          type: inc.type,
          severity: inc.severity,
          timestamp: inc.timestamp,
          status: inc.status,
          confidence: inc.confidence || 0,
        }));
        setIncidents(normalizedIncidents);
        
        if (response.data.total && response.data.limit) {
          setTotalPages(Math.ceil(response.data.total / response.data.limit));
        }
      }
    } catch (error) {
      console.error('Error fetching incidents:', error);
      // Fallback to empty array on error
      setIncidents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (incidentId: string, newStatus: 'investigating' | 'resolved' | 'dismissed') => {
    try {
      const response = await apiService.updateIncidentStatus(incidentId, newStatus);
      if (!response.error) {
        fetchIncidents();
        setShowDropdown(null);
      } else {
        alert(response.error);
      }
    } catch (error) {
      console.error('Error updating incident status:', error);
      alert('Failed to update incident status');
    }
  };

  // Add hover event handlers
  useEffect(() => {
    const handleMouseLeave = (event: MouseEvent) => {
      // Handle filter dropdown
      if (filterRef.current && !filterRef.current.contains(event.relatedTarget as Node)) {
        setShowFilters(false);
      }
      
      // Handle action dropdown
      if (dropdownRef.current && !dropdownRef.current.contains(event.relatedTarget as Node)) {
        setShowDropdown(null);
      }
    };

    const filterElement = filterRef.current;
    const dropdownElement = dropdownRef.current;

    if (filterElement) {
      filterElement.addEventListener('mouseleave', handleMouseLeave);
    }
    if (dropdownElement) {
      dropdownElement.addEventListener('mouseleave', handleMouseLeave);
    }

    return () => {
      if (filterElement) {
        filterElement.removeEventListener('mouseleave', handleMouseLeave);
      }
      if (dropdownElement) {
        dropdownElement.removeEventListener('mouseleave', handleMouseLeave);
      }
    };
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'investigating': return 'text-yellow-600';
      case 'resolved': return 'text-green-600';
      case 'dismissed': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const filteredIncidents = incidents.filter(incident => {
    const studentName = incident.student?.name || incident.student_name || '';
    const examName = incident.exam?.name || incident.exam_name || '';
    
    const matchesSearch = 
      incident.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      examName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.type.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity = activeFilters.severity.length === 0 || 
      activeFilters.severity.includes(incident.severity);
    
    const matchesStatus = activeFilters.status.length === 0 || 
      activeFilters.status.includes(incident.status);
    
    const matchesType = activeFilters.type.length === 0 || 
      activeFilters.type.includes(incident.type);

    return matchesSearch && matchesSeverity && matchesStatus && matchesType;
  });

  const ActionDropdown = ({ incidentId, isFirstRow }: { incidentId: string; isFirstRow: boolean }) => (
    <div 
      className={`absolute right-8 ${
        isFirstRow ? 'top-full mt-2' : 'bottom-full mb-2'
      } w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50`}
      onMouseLeave={() => setShowDropdown(null)}
    >
      <div className="py-1 overflow-hidden">
        <button 
          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-lime-50 hover:text-lime-700 flex items-center gap-2 transition-colors rounded-md mx-1"
          onClick={() => window.open('#', '_blank')}
        >
          View Video
        </button>
        <button 
          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-lime-50 hover:text-lime-700 flex items-center gap-2 transition-colors rounded-md mx-1"
          onClick={() => console.log('Open report')}
        >
          Investigation Report
        </button>
        <button 
          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-lime-50 hover:text-lime-700 flex items-center gap-2 transition-colors rounded-md mx-1"
          onClick={() => {
            const currentStatus = incidents.find(i => i.id === incidentId)?.status;
            if (currentStatus === 'investigating') {
              handleStatusUpdate(incidentId, 'resolved');
            } else if (currentStatus === 'resolved') {
              handleStatusUpdate(incidentId, 'dismissed');
            } else {
              handleStatusUpdate(incidentId, 'investigating');
            }
          }}
        >
          Update Status
        </button>
      </div>
    </div>
  );

  const FilterPanel = () => (
    <div 
      ref={filterRef}
      className="absolute right-0 mt-2 w-64 rounded-md shadow-lg bg-white p-4 z-50"
      onMouseLeave={() => setShowFilters(false)}
    >
      <h3 className="font-medium mb-3">Filter by:</h3>
      
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-medium mb-2">Severity</h4>
          <div className="space-y-2">
            {['low', 'medium', 'high'].map(severity => (
              <label key={severity} className="flex items-center">
                <input
                  type="checkbox"
                  checked={activeFilters.severity.includes(severity)}
                  onChange={(e) => {
                    setActiveFilters(prev => ({
                      ...prev,
                      severity: e.target.checked
                        ? [...prev.severity, severity]
                        : prev.severity.filter(s => s !== severity)
                    }));
                  }}
                  className="rounded border-gray-300 text-lime-600 focus:ring-lime-500"
                />
                <span className="ml-2 text-sm">{severity.charAt(0).toUpperCase() + severity.slice(1)}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium mb-2">Status</h4>
          <div className="space-y-2">
            {['investigating', 'resolved', 'dismissed'].map(status => (
              <label key={status} className="flex items-center">
                <input
                  type="checkbox"
                  checked={activeFilters.status.includes(status)}
                  onChange={(e) => {
                    setActiveFilters(prev => ({
                      ...prev,
                      status: e.target.checked
                        ? [...prev.status, status]
                        : prev.status.filter(s => s !== status)
                    }));
                  }}
                  className="rounded border-gray-300 text-lime-600 focus:ring-lime-500"
                />
                <span className="ml-2 text-sm">{status.charAt(0).toUpperCase() + status.slice(1)}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-gray-900">Incident Review</h1>
              <p className="text-gray-600">Review flagged incidents, analyze evidence, and make determinations</p>
            </div>

            <div className="bg-white rounded-lg shadow">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Incident Reports</h2>
                  <div className="flex space-x-4">
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="Search..."
                        className="pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-lime-500"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                      <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                    </div>
                    <div className="relative">
                      <button 
                        className="flex items-center px-4 py-2 border rounded-lg hover:bg-gray-50"
                        onMouseEnter={() => setShowFilters(true)}
                      >
                        <Filter className="h-5 w-5 mr-2" />
                        Filter
                      </button>
                      {showFilters && <FilterPanel />}
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-sm text-gray-500 border-b">
                        <th className="pb-4">Incident Details</th>
                        <th className="pb-4">Student</th>
                        <th className="pb-4">Exam</th>
                        <th className="pb-4">Type & Severity</th>
                        <th className="pb-4">Timestamp</th>
                        <th className="pb-4">Status</th>
                        <th className="pb-4">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loading ? (
                        <tr>
                          <td colSpan={7} className="text-center py-8 text-gray-500">
                            Loading incidents...
                          </td>
                        </tr>
                      ) : filteredIncidents.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="text-center py-8 text-gray-500">
                            No incidents found
                          </td>
                        </tr>
                      ) : (
                        filteredIncidents.map((incident) => {
                          const studentName = incident.student?.name || incident.student_name || 'Unknown';
                          const studentId = incident.student?.id || incident.student_id || 'N/A';
                          const examName = incident.exam?.name || incident.exam_name || 'Unknown';
                          const instructor = incident.exam?.instructor || incident.instructor || 'N/A';
                          const cameraId = incident.cameraId || incident.camera_id || 'N/A';
                          
                          return (
                            <tr key={incident.id} className="border-b hover:bg-gray-50">
                              <td className="py-4">
                                <div className="font-medium">{incident.id}</div>
                                <div className="text-sm text-gray-500">{cameraId}</div>
                                <div className="text-xs text-gray-400">Confidence: {incident.confidence}%</div>
                              </td>
                              <td className="py-4">
                                <div className="font-medium">{studentName}</div>
                                <div className="text-sm text-gray-500">{studentId}</div>
                              </td>
                              <td className="py-4">
                                <div className="font-medium">{examName}</div>
                                <div className="text-sm text-gray-500">{instructor}</div>
                              </td>
                          <td className="py-4">
                            <div className="font-medium">{incident.type}</div>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(incident.severity)}`}>
                              {incident.severity}
                            </span>
                          </td>
                          <td className="py-4">{incident.timestamp}</td>
                          <td className="py-4">
                            <span className={`font-medium ${getStatusColor(incident.status)}`}>
                              {incident.status}
                            </span>
                          </td>
                          <td className="py-4 relative">
                            <button 
                              className="p-2 hover:bg-gray-100 rounded-full"
                              onMouseEnter={() => setShowDropdown(incident.id)}
                            >
                              <MoreVertical className="h-5 w-5 text-gray-400" />
                            </button>
                            {showDropdown === incident.id && (
                              <ActionDropdown 
                                incidentId={incident.id} 
                                isFirstRow={incident.id === 'INC-001'} 
                              />
                            )}
                          </td>
                        </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-gray-500">
                    Showing {filteredIncidents.length} of {incidents.length} entries
                  </div>
                  {totalPages > 1 && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-600">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Incidents;