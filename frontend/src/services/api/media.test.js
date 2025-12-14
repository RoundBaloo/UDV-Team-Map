import { mediaApi } from './media';
import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

describe('mediaApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    if (global._originalXMLHttpRequest) {
      global.XMLHttpRequest = global._originalXMLHttpRequest;
      delete global._originalXMLHttpRequest;
    }
  });

  test('initUpload вызывает apiClient.post с правильным телом и возвращает результат', async () => {
    const spy = jest.spyOn(apiClient, 'post').mockResolvedValue({ upload_id: '123' });

    const res = await mediaApi.initUpload('image/png');

    expect(spy).toHaveBeenCalledWith(API_ENDPOINTS.MEDIA.INIT_UPLOAD, {
      content_type: 'image/png',
    });
    expect(res).toEqual({ upload_id: '123' });
  });

  test('finalizeUpload вызывает apiClient.post с storage_key и возвращает результат', async () => {
    const spy = jest.spyOn(apiClient, 'post').mockResolvedValue({ success: true });

    const res = await mediaApi.finalizeUpload('some/key.png');

    expect(spy).toHaveBeenCalledWith(API_ENDPOINTS.MEDIA.FINALIZE_UPLOAD, {
      storage_key: 'some/key.png',
    });
    expect(res).toEqual({ success: true });
  });

  test('uploadToPresignedUrl резолвится и вызывает onProgress с процентами', async () => {
    if (!global._originalXMLHttpRequest) {
      global._originalXMLHttpRequest = global.XMLHttpRequest;
    }

    class MockXHR {
      constructor() {
        this.headers = {};
        this.upload = {};
        this.status = 0;
      }
      open(method, url) {
        this._method = method;
        this._url = url;
      }
      setRequestHeader(k, v) {
        this.headers[k] = v;
      }
      send(file) {
        setTimeout(() => {
          if (this.upload.onprogress) {
            this.upload.onprogress({ lengthComputable: true, loaded: 50, total: 100 });
          }
        }, 0);

        setTimeout(() => {
          if (this.upload.onprogress) {
            this.upload.onprogress({ lengthComputable: true, loaded: 75, total: 100 });
          }
        }, 5);

        setTimeout(() => {
          this.status = 200;
          if (typeof this.onload === 'function') this.onload();
        }, 10);
      }
      abort() {}
    }

    global.XMLHttpRequest = MockXHR;

    const progresses = [];
    const onProgress = p => progresses.push(p);

    const fakeFile = { type: 'image/png', size: 100 };
    
    await expect(mediaApi.uploadToPresignedUrl('https://upload.url', fakeFile, onProgress)).resolves.toBeUndefined();

    expect(progresses).toContain(50);
    expect(progresses).toContain(75);
  });

  test('uploadToPresignedUrl отклоняется при статусе >=300 (ошибка сервера)', async () => {
    if (!global._originalXMLHttpRequest) {
      global._originalXMLHttpRequest = global.XMLHttpRequest;
    }

    class MockXHRFail {
      constructor() {
        this.upload = {};
        this.status = 0;
      }
      open() {}
      setRequestHeader() {}
      send() {
        setTimeout(() => {
          this.status = 500;
          if (typeof this.onload === 'function') this.onload();
        }, 0);
      }
    }

    global.XMLHttpRequest = MockXHRFail;

    const fakeFile = { type: 'image/png', size: 100 };

    await expect(mediaApi.uploadToPresignedUrl('https://upload.url', fakeFile)).rejects.toThrow('Upload failed with status 500');
  });

  test('uploadToPresignedUrl отклоняется при сетевой ошибке', async () => {
    if (!global._originalXMLHttpRequest) {
      global._originalXMLHttpRequest = global.XMLHttpRequest;
    }

    class MockXHRError {
      constructor() {
        this.upload = {};
      }
      open() {}
      setRequestHeader() {}
      send() {
        setTimeout(() => {
          if (typeof this.onerror === 'function') this.onerror();
        }, 0);
      }
    }

    global.XMLHttpRequest = MockXHRError;

    const fakeFile = { type: 'image/png', size: 100 };

    await expect(mediaApi.uploadToPresignedUrl('https://upload.url', fakeFile)).rejects.toThrow('Network error during upload');
  });

  test('uploadToPresignedUrl отклоняется при abort', async () => {
    if (!global._originalXMLHttpRequest) {
      global._originalXMLHttpRequest = global.XMLHttpRequest;
    }

    class MockXHRAbort {
      constructor() {
        this.upload = {};
      }
      open() {}
      setRequestHeader() {}
      send() {
        setTimeout(() => {
          if (typeof this.onabort === 'function') this.onabort();
        }, 0);
      }
    }

    global.XMLHttpRequest = MockXHRAbort;

    const fakeFile = { type: 'image/png', size: 100 };

    await expect(mediaApi.uploadToPresignedUrl('https://upload.url', fakeFile)).rejects.toThrow('Upload aborted');
  });
});
