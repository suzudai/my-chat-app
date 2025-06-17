import React from 'react';
import { Model } from '../types';
import ChevronDownIcon from './icons/ChevronDownIcon';

interface ModelSelectorProps {
  models: Model[];
  selectedModelId: string;
  onModelChange: (modelId: string) => void;
  disabled: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ models, selectedModelId, onModelChange, disabled }) => {
  return (
    <div className="relative">
      <select
        value={selectedModelId}
        onChange={(e) => onModelChange(e.target.value)}
        disabled={disabled}
        className="w-full bg-gray-700 text-white pl-3 pr-10 py-2 rounded-md appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-800 disabled:text-gray-500 transition-colors"
      >
        <option value="" disabled>Select a model</option>
        {models.map((model) => (
          <option key={model.id} value={model.id} disabled={model.disabled} className={model.disabled ? "text-gray-500" : ""}>
            {model.name}
          </option>
        ))}
      </select>
      <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
        <ChevronDownIcon className="w-5 h-5 text-gray-400" />
      </div>
    </div>
  );
};

export default ModelSelector;