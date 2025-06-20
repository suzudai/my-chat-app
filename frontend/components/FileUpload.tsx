import React, { useRef, useState } from 'react';
import { ApiResponse } from '../types';

interface FileUploadProps {
  onUploadSuccess: () => void;
  onUploadError: (error: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, onUploadError }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.ms-powerpoint'
  ];

  const allowedExtensions = ['.pdf', '.docx', '.doc', '.pptx', '.ppt'];

  const uploadFile = async (file: File) => {
    if (uploading) return;

    // ファイル形式の検証
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExtensions.includes(fileExtension || '')) {
      onUploadError(`サポートされていないファイル形式です。対応形式: ${allowedExtensions.join(', ')}`);
      return;
    }

    // ファイルサイズの検証（10MB）
    if (file.size > 10 * 1024 * 1024) {
      onUploadError('ファイルサイズが大きすぎます（最大10MB）');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/langchainchatrag/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'アップロードに失敗しました');
      }

      const result: ApiResponse = await response.json();
      
      if (result.success) {
        onUploadSuccess();
      } else {
        onUploadError(result.message);
      }
    } catch (error) {
      onUploadError(error instanceof Error ? error.message : 'アップロードエラーが発生しました');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadFile(file);
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
    
    const file = event.dataTransfer.files[0];
    if (file) {
      uploadFile(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="mb-4">
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-blue-400 bg-blue-900/20'
            : uploading
            ? 'border-gray-500 bg-gray-800'
            : 'border-gray-600 hover:border-gray-500 hover:bg-gray-800'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={!uploading ? handleClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={allowedExtensions.join(',')}
          onChange={handleFileSelect}
          className="hidden"
          disabled={uploading}
        />
        
        {uploading ? (
          <div className="text-blue-400">
            <div className="animate-spin inline-block w-6 h-6 border-2 border-current border-t-transparent rounded-full mb-2"></div>
            <p>アップロード中...</p>
          </div>
        ) : (
          <div className="text-gray-400">
            <div className="text-4xl mb-2">📁</div>
            <p className="text-lg font-medium mb-1">ファイルをドラッグ&ドロップ</p>
            <p className="text-sm">または クリックして選択</p>
            <p className="text-xs mt-2 text-gray-500">
              対応形式: PDF, Word, PowerPoint (最大10MB)
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload; 