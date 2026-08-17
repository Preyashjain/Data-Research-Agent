import React from 'react';
import { Select } from 'antd';

interface AgentSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

const AgentSelector: React.FC<AgentSelectorProps> = ({ value, onChange }) => {
  return (
    <Select
      value={value}
      className="ml-2 mr-5 w-52"
      onChange={onChange}
      options={[
        { value: "data-research-agent", label: "Data Research Agent" },
        { value: "oa-assistant", label: "Legacy OA Assistant" },
        { value: "multi-agent-supervisor", label: "Multi-Agent Supervisor" },
      ]}
    />
  );
};

export default AgentSelector;